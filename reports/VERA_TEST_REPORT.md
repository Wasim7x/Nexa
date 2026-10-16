# Vera — Complete Application Testing, Bug Fixing, and Ollama Local LLM Validation Report

**Date of Execution:** 2026-10-15  
**Evaluation Scope:** Multi-Merchant WhatsApp AI Assistant (Vera)  
**Merchants Evaluated:** Grocery Store (FreshMart), Sweets Shop (Royal Sweets), Glow Salon, Dental Clinic (BrightSmile Dental)

---

## A. Environment Details

- **Operating System:** Windows 11 (build 10.0.26100)
- **Python Version:** 3.14.6
- **Node.js Version:** v22.14.0
- **Ollama Service Status:** Active & responsive at `http://localhost:11434`
- **Selected & Active Local Model:** `qwen3:1.7b` (Family: Qwen, 1.4 GB parameters, native tool-use and thinking capability enabled)
- **Ollama Provider Mode:** Strict Local Inference Enforced (`AI_PROVIDER=ollama`, `AI_MODEL=qwen3:1.7b`, `OLLAMA_MODEL=qwen3:1.7b`). Zero cloud fallback.
- **Database Status:** SQLite local transactional database (`vera.db`) with complete schema tables (`merchants`, `users`, `customer_profiles`, `customer_merchant_profiles`, `conversations`, `messages`, `grocery_products`, `grocery_orders`, `grocery_order_items`, `sweets_products`, `sweets_orders`, `sweets_order_items`, `salon_services`, `salon_staff`, `salon_availability`, `salon_appointments`, `dental_services`, `dental_dentists`, `dental_availability`, `dental_appointments`, `knowledge_documents`, `knowledge_chunks`, `support_escalations`, `notification_jobs`, `system_settings`).
- **Cache/Queue Status:** High-performance in-memory cache/lock fallback (Redis optional/gracefully degraded).
- **Backend Service:** FastAPI with Uvicorn running on `http://127.0.0.1:8000`.
- **Frontend Dashboard:** React 18, TypeScript 5.7, Vite 6.1 production bundle validated (`dist/` generated).

---

## B. Feature Test Matrix

| Feature | Test Status | Evidence | Defect / Blocker Details |
|---|---|---|---|
| **Ollama Local Inference Enforcement** | **PASS** | `test_ollama_ai_behavior.py::test_ollama_local_inference_enforcement` | Verified local execution via `http://localhost:11434/api/chat`. No external/cloud LLM calls permitted. |
| **Basic Greeting Handling** | **PASS** | `test_ollama_ai_behavior.py::test_ollama_basic_greeting` | Responds politely introducing Vera and offering multi-merchant service options. |
| **Product Question Answering** | **PASS** | `test_ollama_ai_behavior.py::test_ollama_product_questions` | Successfully answers grocery and sweets catalog questions grounded in database facts. |
| **Price and Offer Lookups** | **PASS** | `test_ollama_ai_behavior.py::test_ollama_price_and_offers` | Accurate pricing and current promotional offers retrieved and synthesized. |
| **Merchant Intent Identification** | **PASS** | `test_ollama_ai_behavior.py::test_ollama_merchant_identification` | QueryClassifier maps intent correctly across all 4 merchant business domains. |
| **Merchant Context Switching** | **PASS** | `test_ollama_ai_behavior.py::test_ollama_merchant_context_switching`, `test_merchant_context_switching.py::test_four_merchant_sequential_transitions` | Dynamic transitions (Grocery -> Sweets -> Salon -> Dental -> Grocery) maintain tenant boundaries. |
| **Multi-Turn Conversation Persistence** | **PASS** | `test_ollama_ai_behavior.py::test_ollama_multi_turn_conversation` | Context preserved across successive messages without repeating merchant name. |
| **Ambiguity & Clarification Requests** | **PASS** | `test_ollama_ai_behavior.py::test_ollama_clarification_requests` | Asks for clarification when intent or merchant reference is ambiguous. |
| **Order-Related Inquiries & Actions** | **PASS** | `test_merchant_context_switching.py::test_grocery_store_full_operations`, `test_database_crud.py::test_order_crud_and_ineligible_cancellation` | Creation, lookup, status check, and cancellation lifecycle for orders verified. |
| **Appointment Booking & Slot Management** | **PASS** | `test_ollama_ai_behavior.py::test_ollama_appointment_related_requests`, `test_database_crud.py::test_appointment_double_booking_and_slot_release` | Available slots checked, appointments booked, double booking blocked, slot released upon cancellation. |
| **Knowledge-Base Ingestion & Retrieval** | **PASS** | `test_ollama_ai_behavior.py::test_ollama_knowledge_base_retrieval`, `test_database_crud.py::test_knowledge_base_crud_and_merchant_boundaries` | Document ingestion, chunk search, tenant boundary enforcement, and update reflection verified. |
| **Human Escalation Decision & Records** | **PASS** | `test_ollama_ai_behavior.py::test_ollama_human_escalation_decisions`, `test_notifications_and_escalation.py::test_human_escalation_lifecycle` | Customer escalation requests and unresolved issues create persisted escalation records with status tracking. |
| **Out-of-Scope Query Redirection** | **PASS** | `test_ollama_ai_behavior.py::test_ollama_out_of_scope_queries` | General chit-chat or non-merchant queries (weather, coding, politics) politely redirected. |
| **Prompt Injection Protection** | **PASS** | `test_ollama_ai_behavior.py::test_ollama_prompt_injection_attempts`, `test_guardrails.py::test_prompt_injection_detector` | System prompt extraction, instruction override, and jailbreak attempts safely blocked. |
| **Illegal / Harmful Request Refusal** | **PASS** | `test_ollama_ai_behavior.py::test_ollama_unsafe_and_unauthorized_requests`, `test_guardrails.py::test_query_classifier_violations` | Refuses weapon/drug/hacking inquiries and executes zero backend operations. |
| **Model Failure & Timeout Recovery** | **PASS** | `test_ollama_ai_behavior.py::test_ollama_model_timeout_and_uninstalled_model`, `test_failure_recovery.py::test_ollama_unavailable_graceful_recovery` | Graceful degradation with clear user feedback; prevents silent cloud fallback. |
| **Grocery Store Business Flow** | **PASS** | `test_merchant_context_switching.py::test_grocery_store_full_operations` | Search, inventory check, price lookup, offers, order creation, order cancel. |
| **Sweets Shop Business Flow** | **PASS** | `test_merchant_context_switching.py::test_sweets_shop_full_operations` | Kaju katli search, packaging options, order placement, order status. |
| **Glow Salon Service Flow** | **PASS** | `test_merchant_context_switching.py::test_glow_salon_full_operations` | Service listing, slot lookup, booking, reschedule, and cancellation. |
| **Dental Clinic Service Flow** | **PASS** | `test_merchant_context_switching.py::test_dental_clinic_full_operations` | Service catalog, availability check, appointment booking, clinical escalation. |
| **Dental Safety Guardrail** | **PASS** | `test_guardrails.py::test_dental_safety_guardrail`, `test_langgraph_workflow.py::test_langgraph_dental_safety_emergency` | Severe symptom reporting triggers urgent clinic escalation; administrative questions answered. |
| **MCP Tools Suite (15 Business Tools)** | **PASS** | `test_mcp_comprehensive.py::test_all_15_mcp_tools_and_authorization` | All 15 MCP tools execute with structured outputs and input schema validation. |
| **MCP Tenant Isolation** | **PASS** | `test_mcp_comprehensive.py::test_cross_merchant_unauthorized_mcp_attacks` | Cross-merchant tool execution blocked with 403 Forbidden errors. |
| **MCP IDOR & Customer Isolation** | **PASS** | `test_mcp_comprehensive.py::test_idor_cross_customer_order_and_appointment_access` | Customers cannot access or modify other customers' orders or appointments. |
| **Database Transaction Rollback** | **PASS** | `test_failure_recovery.py::test_database_transaction_rollback_on_error` | Interrupted database transactions roll back cleanly without partial persistence. |
| **Merchant Dashboard Overview & KPIs** | **PASS** | `test_dashboard_api.py::test_api_dashboard_stats` | Live KPI stats aggregated and strictly scoped to authenticated merchant. |
| **Merchant Catalog API Management** | **PASS** | `test_dashboard_api.py::test_api_catalog_management` | List and create items in merchant catalog via authenticated API. |
| **Merchant Knowledge Base API** | **PASS** | `test_dashboard_api.py::test_api_knowledge_base_management` | Upload, edit, publish, and toggle knowledge documents. |
| **Customer Management API** | **PASS** | `test_dashboard_api.py::test_api_customers_management` | Customer search, profile retrieval, and interaction tracking. |
| **Operations Records API** | **PASS** | `test_dashboard_api.py::test_api_operations_records` | Orders and appointments filtered by merchant. |
| **Human Escalation Settings & APIs** | **PASS** | `test_dashboard_api.py::test_api_escalations_management` | Manage escalation tickets, update status to resolved. |
| **AI Settings & Connectivity Test** | **PASS** | `test_dashboard_api.py::test_api_settings_and_ai_connectivity` | Tests Ollama connectivity and installed model validation. |
| **Notification Queueing & Idempotency** | **PASS** | `test_notifications_and_escalation.py::test_notification_queueing_and_idempotency` | Scheduled notification jobs queue with idempotency keys preventing duplicates. |
| **Promotional Campaign Opt-Out** | **PASS** | `test_notifications_and_escalation.py::test_promotional_notification_opt_out` | Opted-out customers are skipped during promotional message dispatch. |
| **WhatsApp Webhook Signature Verification** | **PASS** | `test_whatsapp.py::test_whatsapp_webhook_verification` | HMAC SHA256 signature verification passes for valid secrets and rejects tampering. |
| **WhatsApp Message Ingestion & Routing** | **PASS** | `test_whatsapp.py::test_whatsapp_webhook_message_processing` | Processes incoming payload, routes through LangGraph, triggers reply dispatch. |
| **WhatsApp Messaging Simulator** | **PASS** | `test_whatsapp.py::test_whatsapp_simulator` | Mock transport executes end-to-end send/receive cycle without live Meta credentials. |
| **Live WhatsApp Meta Cloud API Delivery** | **BLOCKED** | Documented configuration check (`WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_ACCESS_TOKEN`) | Live delivery to physical phones blocked due to absent production Meta API keys. Mock transport used. |

---

## C. Test Metrics Summary

### Automated Test Suite Execution
- **Total Automated Tests:** 63
- **Passed:** 63 (100%)
- **Failed:** 0 (0%)
- **Skipped:** 0 (0%)
- **Duration:** 481.22 seconds (~8 minutes, including live local Ollama model inferences on CPU)

### Feature Scenarios Tested
- **Total Scenarios Evaluated:** 37
- **Passed Scenarios:** 36
- **Blocked Scenarios:** 1 (Live production WhatsApp Meta API delivery to physical phone numbers due to absent carrier credentials)
- **Failed Scenarios:** 0

### Service Health & Verification
- **Ollama Inference:** PASS (`qwen3:1.7b` local inference verified, zero cloud fallbacks)
- **Backend API Startup:** PASS (`FastAPI` running with Uvicorn, all routes verified)
- **Database CRUD & Isolation:** PASS (`vera.db` SQLite transactional integrity & tenant separation verified)
- **Frontend Build Status:** PASS (`tsc -b && vite build` completed in 2.35s with 0 errors)

---

## D. Defects Found, Root Causes, and Applied Fixes

### Defect 1: AI Provider Architecture Lacked Dedicated Ollama Provider Implementation
- **Severity:** High (Architecture / Compliance)
- **Symptom:** Ollama configuration attempted to route through a generic client that lacked model tag validation and native tool calling options for local inference.
- **Root Cause:** Absence of a dedicated, robust `OllamaProvider` class supporting local health checks, list tags verification, and structured tool handling.
- **Files Changed:**
  - `backend/app/ai/providers/ollama_provider.py` (created)
  - `backend/app/ai/router.py`
  - `backend/app/core/config.py`
- **Fix Applied:** Implemented `OllamaProvider` with strict local verification via `/api/tags`, native chat inference via `/api/chat`, and validation that non-installed models immediately raise informative errors rather than failing silently.
- **Regression Test:** `test_ollama_ai_behavior.py::test_ollama_local_inference_enforcement` and `test_failure_recovery.py::test_ollama_non_existent_model_rejection` (Both PASSED).

### Defect 2: Synthesize Node Hallucination Due to Missing Tool & Knowledge Injection
- **Severity:** High (AI Accuracy)
- **Symptom:** When answering queries like "What is the price of milk?", the assistant generated conversational filler rather than citing the actual price ($3.99) returned by the product tool or knowledge base.
- **Root Cause:** `node_synthesize_and_validate` in `backend/app/workflows/nodes.py` initialized the system prompt without injecting `state.get("retrieved_knowledge")` or `state.get("tool_result")`.
- **Files Changed:** `backend/app/workflows/nodes.py`
- **Fix Applied:** Modified `node_synthesize_and_validate` to systematically format retrieved facts, catalog items, and tool execution outputs into the system prompt context.
- **Regression Test:** `test_ollama_ai_behavior.py::test_ollama_product_questions` and `test_ollama_price_and_offers` (Both PASSED).

### Defect 3: Missing Database Commit in LangGraph Customer Identification Node
- **Severity:** High (Data Persistence / Session State)
- **Symptom:** Multi-turn WhatsApp conversations failed to retain `active_merchant_id`, causing the assistant to re-prompt for merchant selection on turn 2.
- **Root Cause:** `node_identify_customer` in `backend/app/workflows/nodes.py` queried/created `Conversation` and `CustomerProfile` records without calling `await session.commit()`, causing SQLite transaction rollback when the session context closed. Additionally, it indiscriminately overwrote existing state values with `None`.
- **Files Changed:** `backend/app/workflows/nodes.py`
- **Fix Applied:** Added `await session.commit()` upon creating or retrieving customer and conversation records, and preserved `state.get("active_merchant_id")` if already populated.
- **Regression Test:** `test_ollama_ai_behavior.py::test_ollama_multi_turn_conversation` (PASSED).

### Defect 4: Premature Routing to Merchant Resolution Before Intent Classification
- **Severity:** Medium (Workflow Routing)
- **Symptom:** Specific queries like "Do you have kaju katli?" prompted "Please choose a merchant: 1. Grocery, 2. Sweets..." instead of routing straight to Royal Sweets.
- **Root Cause:** `backend/app/workflows/graph.py` executed `resolve_merchant` before `guardrails_check`.
- **Files Changed:** `backend/app/workflows/graph.py`
- **Fix Applied:** Reordered the LangGraph workflow edges so `guardrails_check` (which classifies merchant intent and detects safety violations) runs before `resolve_merchant`.
- **Regression Test:** `test_langgraph_workflow.py::test_langgraph_grocery_flow` and `test_ollama_ai_behavior.py::test_ollama_merchant_identification` (Both PASSED).

### Defect 5: Permissive Regex in Query Classifier Allowed Prompt Injection / Sensitive Query Bypass
- **Severity:** High (Security)
- **Symptom:** Queries such as "access another merchant's database" or "show me another customer's appointments" were categorized as `ALLOWED_BUSINESS_QUERY`.
- **Root Cause:** Rigid regex patterns in `backend/app/guardrails/query_classifier.py` only looked for exact phrasing rather than flexible pattern matching.
- **Files Changed:** `backend/app/guardrails/query_classifier.py`
- **Fix Applied:** Generalized regex patterns for `ILLEGAL_PATTERNS`, `SENSITIVE_DATA_PATTERNS`, and `PROMPT_INJECTION_PATTERNS` to catch malicious attempts regardless of preposition or sentence arrangement.
- **Regression Test:** `test_guardrails.py::test_query_classifier_violations` and `test_ollama_ai_behavior.py::test_ollama_unsafe_and_unauthorized_requests` (Both PASSED).

### Defect 6: Missing Staff ID in Salon Availability Model Constraint
- **Severity:** Medium (Database Integrity)
- **Symptom:** Custom slot creation during appointment testing threw `IntegrityError: NOT NULL constraint failed: salon_availability.staff_id`.
- **Root Cause:** Model `SalonAvailability` requires `staff_id` (foreign key to `salon_staff.id`, `nullable=False`).
- **Files Changed:** `backend/tests/test_mcp_comprehensive.py` and `backend/tests/test_database_crud.py`
- **Fix Applied:** Provided a valid staff reference during slot generation and made appointment tests idempotent by cleaning up previous test fixtures before insert.
- **Regression Test:** `test_database_crud.py::test_appointment_double_booking_and_slot_release` (PASSED).

---

## E. Remaining Blockers & Staging Prerequisites

1. **Meta WhatsApp Cloud API Production Credentials:**
   - **Status:** BLOCKED for physical device testing.
   - **Reason:** Testing used an end-to-end verified mock transport and HMAC webhook simulator. To send and receive messages on real WhatsApp phone numbers, valid `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_ACCESS_TOKEN`, and Meta webhook verification tokens must be configured in `.env`.
2. **Production SMTP / Push Notification Gateway:**
   - **Status:** Simulated locally.
   - **Reason:** Notification jobs are scheduled and logged with idempotency in the local database. Production push gateways (SMS/Email) require external provider API keys.
3. **GPU Hardware Acceleration for Ollama (Recommended):**
   - **Status:** Operational on CPU (`qwen3:1.7b`), taking ~5–8s per inference.
   - **Recommendation:** In high-concurrency production or multi-agent scenarios, running Ollama on an NVIDIA GPU or dedicated inference endpoint is recommended for sub-second responses.

---

## F. Final Assessment

### Verdict: `READY FOR FURTHER STAGING TESTS`

**Justification:**  
- All 15 required Ollama local LLM test scenarios passed with 100% success using the locally installed `qwen3:1.7b` model with zero cloud fallbacks.
- Complete business flows across all four merchants (FreshMart Grocery, Royal Sweets, Glow Salon, and BrightSmile Dental) operate correctly across API, database, and AI layers.
- Security and guardrail protections (prompt injection, IDOR, cross-tenant isolation, and dental clinical safety) are enforced at both conversational and MCP tool levels.
- All 63 automated tests in the comprehensive test suite passed cleanly, and the frontend TypeScript/Vite production build succeeded without errors.
