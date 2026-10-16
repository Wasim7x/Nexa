import re
from typing import Tuple, Optional

# Phone number regex for international WhatsApp E.164-like numbers
PHONE_CLEAN_REGEX = re.compile(r"[^\d+]")
E164_REGEX = re.compile(r"^\+?[1-9]\d{7,14}$")

class InputValidator:
    """Validates and normalizes incoming user and webhook inputs."""

    MAX_MESSAGE_LENGTH = 2000
    MIN_MESSAGE_LENGTH = 1

    @classmethod
    def normalize_phone_number(cls, phone: str) -> str:
        """
        Normalize a phone number to standard E.164 format.
        E.g. '+1 (555) 123-4567' -> '+15551234567'
        '15551234567' -> '+15551234567'
        """
        if not phone:
            raise ValueError("Phone number cannot be empty")
        
        # Remove whitespace, parentheses, dashes, dots
        cleaned = PHONE_CLEAN_REGEX.sub("", phone.strip())
        if not cleaned.startswith("+"):
            cleaned = "+" + cleaned
            
        if not E164_REGEX.match(cleaned):
            raise ValueError(f"Invalid phone number format: {phone}")
            
        return cleaned

    @classmethod
    def sanitize_message_text(cls, text: str) -> Tuple[bool, str, Optional[str]]:
        """
        Sanitize message text and perform character/length checks.
        Returns: (is_valid, sanitized_text, error_message)
        """
        if text is None:
            return False, "", "Message cannot be empty."

        # Strip null bytes and non-printable control characters (except newline, tab, carriage return)
        sanitized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text).strip()

        if len(sanitized) < cls.MIN_MESSAGE_LENGTH:
            return False, "", "Message content is empty or contains only whitespace/control characters."

        if len(sanitized) > cls.MAX_MESSAGE_LENGTH:
            return False, sanitized[:cls.MAX_MESSAGE_LENGTH], f"Message exceeds maximum allowed length of {cls.MAX_MESSAGE_LENGTH} characters."

        # Detect repeated character flood (e.g. 'aaaaaaaaaa...' 80+ times)
        if re.search(r"(.)\1{79,}", sanitized):
            return False, "", "Excessive character repetition detected."

        return True, sanitized, None
