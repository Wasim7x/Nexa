import re
from typing import Tuple, List, Optional
from pydantic import BaseModel

class OutputValidationResult(BaseModel):
    is_safe: bool
    sanitized_text: str
    redacted_elements: List[str] = []
    error_reason: Optional[str] = None

class OutputValidator:
    """
    Scans AI responses before delivering to WhatsApp.
    Prevents secret leakage, system token leakage, and cross-tenant data disclosure.
    """

    SECRET_PATTERNS = [
        (r"(AIzaSy[0-9A-Za-z-_]{33})", "Google API Key"),
        (r"(sk-[a-zA-Z0-9]{32,})", "OpenAI / Generic API Key"),
        (r"(gsk_[a-zA-Z0-9]{30,})", "Groq API Key"),
        (r"(ghp_[a-zA-Z0-9]{36})", "GitHub Token"),
        (r"(EAAB[0-9A-Za-z]{30,})", "Meta WhatsApp Access Token"),
        (r"(postgres(ql)?:\/\/[^\s]+)", "Database connection URI"),
        (r"(sqlite:\/\/[^\s]+)", "Database connection URI")
    ]

    COMPILED_SECRETS = [(re.compile(p), name) for p, name in SECRET_PATTERNS]

    SYSTEM_LEAK_PATTERNS = [
        re.compile(r"my\s+instructions\s+are\s+to\b", re.IGNORECASE),
        re.compile(r"i\s+am\s+programmed\s+with\s+the\s+system\s+prompt\b", re.IGNORECASE),
        re.compile(r"here\s+is\s+my\s+full\s+system\s+prompt:\b", re.IGNORECASE)
    ]

    @classmethod
    def validate(cls, text: str, active_merchant_name: Optional[str] = None) -> OutputValidationResult:
        """Sanitize and validate an outgoing AI message."""
        if not text:
            return OutputValidationResult(is_safe=True, sanitized_text="")

        output = text
        redacted = []

        # 1. Check for API keys and connection strings
        for pattern, secret_type in cls.COMPILED_SECRETS:
            matches = pattern.findall(output)
            if matches:
                redacted.append(secret_type)
                output = pattern.sub("[REDACTED SECRET]", output)

        # 2. Check for system prompt disclosure leaks
        for pattern in cls.SYSTEM_LEAK_PATTERNS:
            if pattern.search(output):
                redacted.append("System Prompt Disclosure")
                return OutputValidationResult(
                    is_safe=False,
                    sanitized_text="I am here to assist you with our products, services, and bookings.",
                    redacted_elements=redacted,
                    error_reason="Attempted disclosure of system instructions"
                )

        return OutputValidationResult(
            is_safe=True,
            sanitized_text=output,
            redacted_elements=redacted
        )

    @classmethod
    def verify_tool_claim(cls, response_text: str, tool_executed: bool, tool_success: bool) -> str:
        """
        Anti-hallucination guardrail:
        If model claims 'Your order has been placed' or 'Your appointment has been booked'
        without a successful tool execution, reject the false claim.
        """
        lowered = response_text.lower()
        claims_booking = any(phrase in lowered for phrase in ["has been booked", "successfully booked", "confirmed your appointment"])
        claims_order = any(phrase in lowered for phrase in ["order has been placed", "order has been confirmed", "order is confirmed"])

        if (claims_booking or claims_order) and (not tool_executed or not tool_success):
            return (
                "I apologize, but I could not confirm your reservation or order at this moment. "
                "Please verify your details or let me know if you would like me to try again."
            )
        return response_text
