import json
import logging
import re
from datetime import date, time, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import select

from backend.app.core.database import AsyncSessionLocal
from backend.app.workflows.state import VeraWorkflowState
from backend.app.guardrails.input_validator import InputValidator
from backend.app.guardrails.prompt_injection_detector import PromptInjectionDetector
from backend.app.guardrails.query_classifier import QueryClassifier, QueryCategory
from backend.app.guardrails.dental_safety import DentalSafetyGuardrail
from backend.app.guardrails.policy_engine import PolicyEngine
from backend.app.guardrails.output_validator import OutputValidator
from backend.app.guardrails.rate_limiter import global_rate_limiter
from backend.app.guardrails.audit_logger import AuditLogger
from backend.app.mcp.context import MCPCallContext
from backend.app.mcp.server import execute_mcp_tool
from backend.app.services.customer_service import CustomerService
from backend.app.models.shared import Merchant, KnowledgeDocument, Message, Conversation
from backend.app.ai.router import get_ai_provider

logger = logging.getLogger("vera.workflows")

async def node_input_validation(state: VeraWorkflowState) -> VeraWorkflowState:
    """Step 1: Sanitize input, normalize phone, and check rate limits."""
    raw_text = state.get("raw_message", "")
    phone = state.get("sender_phone", "")

    # Check rate limit
    is_limited, cooldown = global_rate_limiter.is_rate_limited(phone)
    if is_limited:
        return {
            **state,
            "rate_limited": True,
            "response_text": f"You are sending messages too quickly. Please wait {cooldown} seconds before sending another message."
        }

    # Sanitize text
    is_valid, clean_text, err = InputValidator.sanitize_message_text(raw_text)
    if not is_valid:
        return {
            **state,
            "error_message": err,
            "response_text": err or "Invalid message format."
        }

    return {
        **state,
        "clean_message": clean_text,
        "rate_limited": False
    }

async def node_identify_customer(state: VeraWorkflowState) -> VeraWorkflowState:
    """Step 2: Authenticate/identify customer safely with conflict handling."""
    if state.get("rate_limited") or state.get("error_message"):
        return state

    phone = state.get("sender_phone")
    async with AsyncSessionLocal() as session:
        customer = await CustomerService.get_or_create_customer(session, whatsapp_phone=phone)
        conversation = await CustomerService.get_or_create_conversation(session, customer.id)
        active_merchant = conversation.active_merchant_id or state.get("active_merchant_id")
        await session.commit()

        return {
            **state,
            "customer_id": customer.id,
            "customer_name": customer.name or "Customer",
            "conversation_id": conversation.id,
            "active_merchant_id": active_merchant
        }

async def node_guardrails_check(state: VeraWorkflowState) -> VeraWorkflowState:
    """Step 3: Run multi-layered guardrails (injection, classification, dental safety)."""
    if state.get("rate_limited") or state.get("error_message"):
        return state

    clean_text = state.get("clean_message", "")
    active_merchant = state.get("active_merchant_id")

    # 1. Prompt Injection
    inj_res = PromptInjectionDetector.analyze(clean_text)
    if inj_res.is_injection:
        await AuditLogger.log_event(
            action="GUARDRAIL_PROMPT_INJECTION_BLOCKED",
            resource_type="message",
            customer_phone=state.get("sender_phone"),
            merchant_id=active_merchant,
            details={"pattern": inj_res.trigger_pattern, "reason": inj_res.reason}
        )
        return {
            **state,
            "is_guardrail_violation": True,
            "query_category": QueryCategory.PROMPT_INJECTION.value,
            "guardrail_response": PolicyEngine.PROMPT_INJECTION_RESPONSE,
            "response_text": PolicyEngine.PROMPT_INJECTION_RESPONSE
        }

    # 2. Query Classification
    cls_res = QueryClassifier.classify(clean_text, active_merchant_id=active_merchant)
    state_updates: Dict[str, Any] = {
        "query_category": cls_res.category.value,
        "is_guardrail_violation": False
    }

    if cls_res.is_switch_context and cls_res.detected_merchant_intent:
        state_updates["context_switched"] = True
        state_updates["active_merchant_id"] = cls_res.detected_merchant_intent
    elif cls_res.detected_merchant_intent and not active_merchant:
        state_updates["active_merchant_id"] = cls_res.detected_merchant_intent

    # Handle explicit violations
    if cls_res.category in [
        QueryCategory.ILLEGAL_REQUEST,
        QueryCategory.HARMFUL_REQUEST,
        QueryCategory.OUT_OF_SCOPE_QUERY,
        QueryCategory.SENSITIVE_DATA_REQUEST
    ]:
        pol_msg = PolicyEngine.get_policy_response(cls_res.category)
        await AuditLogger.log_event(
            action=f"GUARDRAIL_{cls_res.category.value}_BLOCKED",
            resource_type="message",
            customer_phone=state.get("sender_phone"),
            merchant_id=state_updates.get("active_merchant_id") or active_merchant,
            details={"explanation": cls_res.explanation}
        )
        return {
            **state,
            **state_updates,
            "is_guardrail_violation": True,
            "guardrail_response": pol_msg,
            "response_text": pol_msg
        }

    # 3. Dental Clinic Safety Guardrail
    current_merchant = state_updates.get("active_merchant_id") or active_merchant
    if current_merchant == "dental-clinic":
        dental_res = DentalSafetyGuardrail.evaluate(clean_text)
        if dental_res.is_clinical_query:
            await AuditLogger.log_event(
                action="GUARDRAIL_DENTAL_SAFETY_TRIGGERED",
                resource_type="message",
                customer_phone=state.get("sender_phone"),
                merchant_id="dental-clinic",
                details={"is_emergency": dental_res.is_emergency, "reason": dental_res.reason}
            )
            return {
                **state,
                **state_updates,
                "dental_safety_triggered": True,
                "dental_safety_response": dental_res.refusal_message,
                "response_text": dental_res.refusal_message
            }

    return {**state, **state_updates}

async def node_merchant_resolution(state: VeraWorkflowState) -> VeraWorkflowState:
    """Step: Resolve merchant context or request clarification."""
    if state.get("is_guardrail_violation") or state.get("dental_safety_triggered") or state.get("rate_limited"):
        return state

    active_merchant = state.get("active_merchant_id")
    referral_slug = state.get("referral_merchant_slug")

    # If referral slug provided (e.g. from merchant QR code / WhatsApp link ?ref=dental)
    if referral_slug:
        slug_to_id = {
            "grocery": "grocery-store",
            "sweets": "sweets-shop",
            "salon": "glow-salon",
            "dental": "dental-clinic"
        }
        ref_id = slug_to_id.get(referral_slug.lower())
        if ref_id:
            active_merchant = ref_id

    # If still no merchant resolved, prompt customer to choose
    if not active_merchant:
        return {
            **state,
            "response_text": PolicyEngine.MERCHANT_SELECTION_PROMPT
        }

    return {
        **state,
        "active_merchant_id": active_merchant
    }

async def node_retrieve_context(state: VeraWorkflowState) -> VeraWorkflowState:
    """Step 5: Retrieve merchant-specific knowledge base documents."""
    if state.get("response_text"):  # Guardrail or clarification already decided
        return state

    merchant_id = state.get("active_merchant_id")
    clean_text = state.get("clean_message", "").lower()

    docs = []
    async with AsyncSessionLocal() as session:
        stmt = select(KnowledgeDocument).where(
            KnowledgeDocument.merchant_id == merchant_id,
            KnowledgeDocument.is_published == True
        )
        res = await session.execute(stmt)
        all_docs = res.scalars().all()

        for d in all_docs:
            # Simple keyword relevance filter
            words = [w for w in clean_text.split() if len(w) > 3]
            if not words or any(w in d.content.lower() or w in d.title.lower() for w in words):
                docs.append({"title": d.title, "content": d.content})

    return {
        **state,
        "retrieved_knowledge": docs
    }

async def node_execute_mcp_tools(state: VeraWorkflowState) -> VeraWorkflowState:
    """Step 6: Determine and execute authorized MCP business tools."""
    if state.get("response_text"):
        return state

    merchant_id = state.get("active_merchant_id")
    customer_id = state.get("customer_id")
    phone = state.get("sender_phone")
    clean_text = state.get("clean_message", "").lower()

    ctx = MCPCallContext(
        merchant_id=merchant_id,
        customer_id=customer_id,
        customer_phone=phone,
        conversation_id=state.get("conversation_id")
    )

    async with AsyncSessionLocal() as session:
        tool_call_info = None
        tool_result = None

        # 1. Human escalation requested
        if any(h in clean_text for h in ["human", "support agent", "talk to human", "speak to representative", "dispute", "talk to someone", "representative"]):
            res = await execute_mcp_tool(
                tool_name="create_support_escalation",
                arguments={"reason": clean_text, "category": "general"},
                ctx=ctx,
                session=session
            )
            return {
                **state,
                "is_escalated": True,
                "tool_call": {"tool_name": "create_support_escalation"},
                "tool_result": res,
                "response_text": res.get("data", {}).get("customer_message") or "Connecting you to a human assistant."
            }

        # 2. Promotions & Offers lookup
        if any(w in clean_text for w in ["offer", "discount", "special", "deal", "promo", "sale"]) and merchant_id in ["grocery-store", "sweets-shop"]:
            res = await execute_mcp_tool(
                tool_name="get_active_offers",
                arguments={},
                ctx=ctx,
                session=session
            )
            tool_call_info = {"tool_name": "get_active_offers"}
            tool_result = res

        # 3. Order status lookup
        elif "order" in clean_text and any(w in clean_text for w in ["status", "track", "where is", "check", "my order"]):
            order_match = re.search(r"ORD-[\w-]+", state.get("clean_message", ""), re.IGNORECASE)
            if order_match:
                ord_num = order_match.group(0).upper()
                res = await execute_mcp_tool(
                    tool_name="get_order",
                    arguments={"order_number": ord_num},
                    ctx=ctx,
                    session=session
                )
                tool_call_info = {"tool_name": "get_order"}
                tool_result = res

        # 4. Service catalog lookup (salon / dental)
        elif any(w in clean_text for w in ["service", "services", "menu", "treatment", "facial", "haircut", "cleaning", "whitening"]) and merchant_id in ["glow-salon", "dental-clinic"]:
            res = await execute_mcp_tool(
                tool_name="list_services",
                arguments={},
                ctx=ctx,
                session=session
            )
            tool_call_info = {"tool_name": "list_services"}
            tool_result = res

        # 5. Product Search / Catalog lookup (grocery / sweets)
        elif any(w in clean_text for w in ["search", "price", "catalog", "do you have", "cost of", "how much", "stock", "milk", "sweet", "kaju katli", "ladoo", "halwa", "item", "product"]):
            # Extract product query if available
            res = await execute_mcp_tool(
                tool_name="search_products",
                arguments={},
                ctx=ctx,
                session=session
            )
            tool_call_info = {"tool_name": "search_products"}
            tool_result = res

        # 6. Available slots lookup (salon / dental)
        elif any(w in clean_text for w in ["slot", "opening", "available", "appointment", "time", "schedule", "book", "tomorrow"]):
            res = await execute_mcp_tool(
                tool_name="check_available_slots",
                arguments={},
                ctx=ctx,
                session=session
            )
            tool_call_info = {"tool_name": "check_available_slots"}
            tool_result = res

        return {
            **state,
            "tool_call": tool_call_info,
            "tool_result": tool_result
        }

async def node_synthesize_and_validate(state: VeraWorkflowState) -> VeraWorkflowState:
    """Step 7: Synthesize response with AI provider and validate output."""
    if state.get("response_text"):
        # Still validate through OutputValidator to ensure safety
        v_res = OutputValidator.validate(state["response_text"])
        return {**state, "response_text": v_res.sanitized_text}

    merchant_id = state.get("active_merchant_id")
    clean_text = state.get("clean_message", "")
    knowledge = state.get("retrieved_knowledge", [])
    tool_result = state.get("tool_result")
    tool_call = state.get("tool_call")

    # Generate response via configured AI provider
    provider = get_ai_provider()
    system_prompt = (
        f"You are Vera, the official AI WhatsApp assistant for {merchant_id}. "
        "Answer the customer's query clearly, politely, and concisely (under 3 sentences). "
        "Strict Rule: Rely ONLY on the verified Store Knowledge and Authoritative Tool Data provided below. "
        "Never invent prices, stock numbers, or appointment slots. If information is not in the data, state that helpfully."
    )

    context_sections = []
    if knowledge:
        k_lines = [f"- {d.get('title')}: {d.get('content')}" for d in knowledge]
        context_sections.append("Verified Store Knowledge:\n" + "\n".join(k_lines))

    if tool_result:
        t_name = tool_call.get("tool_name") if tool_call else "business_tool"
        data_str = json.dumps(tool_result, default=str)
        context_sections.append(f"Authoritative Tool Data ({t_name}):\n{data_str}")

    if context_sections:
        system_prompt += "\n\n" + "\n\n".join(context_sections)

    ai_resp = await provider.generate_response(
        messages=[{"role": "user", "content": clean_text}],
        system_prompt=system_prompt
    )

    raw_output = ai_resp.content

    # Output guardrail validation
    val_res = OutputValidator.validate(raw_output)
    final_output = val_res.sanitized_text

    # Anti-hallucination check
    has_tool = state.get("tool_call") is not None
    tool_ok = (tool_result.get("success") is True) if tool_result else False
    final_output = OutputValidator.verify_tool_claim(final_output, tool_executed=has_tool, tool_success=tool_ok)

    return {
        **state,
        "response_text": final_output
    }

async def node_persist_and_reply(state: VeraWorkflowState) -> VeraWorkflowState:
    """Step 8: Persist message history and update conversation merchant context."""
    conversation_id = state.get("conversation_id")
    merchant_id = state.get("active_merchant_id")
    raw_text = state.get("raw_message", "")
    reply_text = state.get("response_text", "")

    if conversation_id and raw_text and reply_text:
        try:
            async with AsyncSessionLocal() as session:
                # 1. Inbound customer message
                in_msg = Message(
                    conversation_id=conversation_id,
                    merchant_id=merchant_id,
                    sender_type="customer",
                    direction="inbound",
                    content=raw_text,
                    message_metadata={
                        "category": state.get("query_category"),
                        "tool_called": state.get("tool_call") is not None
                    }
                )
                session.add(in_msg)

                # 2. Outbound assistant reply
                out_msg = Message(
                    conversation_id=conversation_id,
                    merchant_id=merchant_id,
                    sender_type="ai_assistant",
                    direction="outbound",
                    content=reply_text
                )
                session.add(out_msg)

                # 3. Update conversation active merchant
                convo_stmt = select(Conversation).where(Conversation.id == conversation_id)
                convo_res = await session.execute(convo_stmt)
                convo = convo_res.scalars().first()
                if convo:
                    if merchant_id:
                        convo.active_merchant_id = merchant_id
                    if state.get("is_escalated"):
                        convo.status = "awaiting_human"

                await session.commit()
        except Exception as e:
            logger.error(f"Error persisting messages: {e}")

    return state
