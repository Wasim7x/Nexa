import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import AsyncSessionLocal
from backend.app.models.shared import AuditLog

logger = logging.getLogger("vera.audit")

class AuditLogger:
    """Records security and business audit events safely."""

    @classmethod
    async def log_event(
        cls,
        action: str,
        resource_type: str,
        merchant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        customer_phone: Optional[str] = None,
        resource_id: Optional[str] = None,
        status: str = "success",
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> None:
        """Persist an audit log entry."""
        # Sanitize details to avoid logging raw secrets
        safe_details = {}
        if details:
            for k, v in details.items():
                if any(sec in k.lower() for sec in ["key", "token", "password", "secret", "auth"]):
                    safe_details[k] = "[REDACTED]"
                else:
                    safe_details[k] = v

        try:
            async with AsyncSessionLocal() as session:
                entry = AuditLog(
                    merchant_id=merchant_id,
                    user_id=user_id,
                    customer_phone=customer_phone,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    status=status,
                    details_json=safe_details,
                    ip_address=ip_address
                )
                session.add(entry)
                await session.commit()
        except Exception as e:
            logger.error(f"Failed to record audit log: {e}")
