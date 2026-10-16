from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
from backend.app.workflows.state import VeraWorkflowState
from backend.app.workflows.nodes import (
    node_input_validation,
    node_identify_customer,
    node_merchant_resolution,
    node_guardrails_check,
    node_retrieve_context,
    node_execute_mcp_tools,
    node_synthesize_and_validate,
    node_persist_and_reply
)

def create_vera_workflow() -> StateGraph:
    """Build the LangGraph state machine for Vera."""
    workflow = StateGraph(VeraWorkflowState)

    # Add Nodes
    workflow.add_node("validate_input", node_input_validation)
    workflow.add_node("identify_customer", node_identify_customer)
    workflow.add_node("resolve_merchant", node_merchant_resolution)
    workflow.add_node("guardrails_check", node_guardrails_check)
    workflow.add_node("retrieve_context", node_retrieve_context)
    workflow.add_node("execute_mcp_tools", node_execute_mcp_tools)
    workflow.add_node("synthesize_and_validate", node_synthesize_and_validate)
    workflow.add_node("persist_and_reply", node_persist_and_reply)

    # Define linear graph execution
    workflow.add_edge(START, "validate_input")
    workflow.add_edge("validate_input", "identify_customer")
    workflow.add_edge("identify_customer", "guardrails_check")
    workflow.add_edge("guardrails_check", "resolve_merchant")
    workflow.add_edge("resolve_merchant", "retrieve_context")
    workflow.add_edge("retrieve_context", "execute_mcp_tools")
    workflow.add_edge("execute_mcp_tools", "synthesize_and_validate")
    workflow.add_edge("synthesize_and_validate", "persist_and_reply")
    workflow.add_edge("persist_and_reply", END)

    return workflow.compile()

# Compile global app workflow
vera_graph = create_vera_workflow()

async def process_whatsapp_message(
    sender_phone: str,
    message_text: str,
    referral_merchant_slug: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main entry point for processing incoming WhatsApp messages.
    Invoked by WhatsApp Cloud API webhook receiver.
    """
    initial_state: VeraWorkflowState = {
        "sender_phone": sender_phone,
        "raw_message": message_text,
        "referral_merchant_slug": referral_merchant_slug,
        "retrieved_knowledge": [],
        "security_events": [],
        "rate_limited": False,
        "is_guardrail_violation": False,
        "dental_safety_triggered": False,
        "is_escalated": False,
        "context_switched": False
    }

    final_state = await vera_graph.ainvoke(initial_state)

    return {
        "sender_phone": final_state.get("sender_phone"),
        "customer_id": final_state.get("customer_id"),
        "active_merchant_id": final_state.get("active_merchant_id"),
        "response_text": final_state.get("response_text", ""),
        "query_category": final_state.get("query_category"),
        "is_guardrail_violation": final_state.get("is_guardrail_violation", False),
        "dental_safety_triggered": final_state.get("dental_safety_triggered", False),
        "is_escalated": final_state.get("is_escalated", False),
        "context_switched": final_state.get("context_switched", False),
        "tool_called": final_state.get("tool_call") is not None
    }
