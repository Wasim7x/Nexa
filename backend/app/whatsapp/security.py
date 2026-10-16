import hmac
import hashlib
import time
from typing import Set, Dict
from backend.app.core.config import settings

class WhatsAppSecurity:
    """Handles HMAC SHA256 webhook verification and message deduplication."""

    _processed_message_ids: Dict[str, float] = {}
    DEDUPLICATION_TTL = 3600  # 1 hour

    @classmethod
    def verify_webhook_signature(cls, payload_bytes: bytes, signature_header: str) -> bool:
        """
        Verify X-Hub-Signature-256 header against WHATSAPP_APP_SECRET.
        If no app secret configured in development, passes safely.
        """
        if not settings.WHATSAPP_APP_SECRET:
            # Safe development mode when Meta App Secret is not yet configured
            return True

        if not signature_header or not signature_header.startswith("sha256="):
            return False

        expected_sig = signature_header[7:]
        computed_sig = hmac.new(
            key=settings.WHATSAPP_APP_SECRET.encode("utf-8"),
            msg=payload_bytes,
            digestmod=hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(computed_sig, expected_sig)

    @classmethod
    def is_duplicate_message(cls, message_id: str) -> bool:
        """
        Check if a WhatsApp message_id was already processed.
        Prevents duplicate actions from webhook retries.
        """
        if not message_id:
            return False

        now = time.time()
        # Clean expired IDs
        cls._processed_message_ids = {
            m_id: ts for m_id, ts in cls._processed_message_ids.items()
            if now - ts < cls.DEDUPLICATION_TTL
        }

        if message_id in cls._processed_message_ids:
            return True

        cls._processed_message_ids[message_id] = now
        return False
