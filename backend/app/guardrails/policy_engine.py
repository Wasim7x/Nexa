from typing import Optional
from backend.app.guardrails.query_classifier import QueryCategory

class PolicyEngine:
    """Generates policy responses for guardrail trigger events and redirection."""

    OUT_OF_SCOPE_RESPONSE = (
        "I'm here to assist with products, services, pricing, offers, orders, and appointments "
        "for our partnered merchants (FreshMart Grocery, Royal Sweets, Glow Salon, and SmileCare Dental Clinic). "
        "How can I help you today?"
    )

    PROMPT_INJECTION_RESPONSE = (
        "I cannot comply with requests that modify my operational instructions or bypass security boundaries. "
        "Please let me know which merchant or service you'd like help with."
    )

    ILLEGAL_HARMFUL_RESPONSE = (
        "I cannot assist with requests involving illegal activities, harmful substances, or security exploits. "
        "I am dedicated to serving customers with legitimate business inquiries."
    )

    SENSITIVE_DATA_RESPONSE = (
        "For privacy and security, I cannot disclose personal information, order records, or data belonging to other customers. "
        "I can only help you with your own verified orders and appointments."
    )

    MERCHANT_SELECTION_PROMPT = (
        "Hello! I am Nexa, your multi-merchant assistant. Which merchant would you like to interact with?\n"
        "1️⃣ FreshMart Grocery (groceries & pantry)\n"
        "2️⃣ Royal Sweets & Delights (mithai & gift hampers)\n"
        "3️⃣ Glow Salon (hair, facials & spa)\n"
        "4️⃣ SmileCare Dental Clinic (checkups & cleanings)"
    )

    @classmethod
    def get_policy_response(cls, category: QueryCategory) -> Optional[str]:
        """Return standardized safe response based on query category violation."""
        if category == QueryCategory.OUT_OF_SCOPE_QUERY:
            return cls.OUT_OF_SCOPE_RESPONSE
        elif category == QueryCategory.PROMPT_INJECTION:
            return cls.PROMPT_INJECTION_RESPONSE
        elif category in (QueryCategory.ILLEGAL_REQUEST, QueryCategory.HARMFUL_REQUEST):
            return cls.ILLEGAL_HARMFUL_RESPONSE
        elif category == QueryCategory.SENSITIVE_DATA_REQUEST:
            return cls.SENSITIVE_DATA_RESPONSE
        elif category == QueryCategory.AMBIGUOUS_QUERY:
            return cls.MERCHANT_SELECTION_PROMPT
        return None
