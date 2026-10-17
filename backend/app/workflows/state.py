from typing import TypedDict, Optional, List, Dict, Any

class NexaWorkflowState(TypedDict, total=False):
    # Customer & Channel Info
    sender_phone: str
    raw_message: str
    clean_message: str
    customer_id: Optional[str]
    customer_name: Optional[str]
    active_merchant_id: Optional[str]
    referral_merchant_slug: Optional[str]
    conversation_id: Optional[str]

    # Guardrails & Classification
    query_category: Optional[str]
    is_guardrail_violation: bool
    guardrail_response: Optional[str]
    dental_safety_triggered: bool
    dental_safety_response: Optional[str]
    rate_limited: bool

    # Multi-tenant Context
    context_switched: bool
    retrieved_knowledge: List[Dict[str, Any]]

    # Tool Execution
    tool_call: Optional[Dict[str, Any]]
    tool_result: Optional[Dict[str, Any]]
    is_escalated: bool

    # Output & Persistence
    response_text: str
    error_message: Optional[str]
    security_events: List[str]
    active_merchant_id: Optional[str]

# Backward compatibility alias
VeraWorkflowState = NexaWorkflowState
