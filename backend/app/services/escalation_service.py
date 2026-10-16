from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.models.shared import SupportEscalation, Conversation, MerchantSettings, Merchant

class EscalationService:
    """Manages customer query escalations to human staff."""

    @classmethod
    async def create_escalation(
        cls,
        session: AsyncSession,
        merchant_id: str,
        customer_id: str,
        reason: str,
        category: str = "general",
        urgency: str = "medium",
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a support escalation and update conversation state to awaiting_human."""
        escalation = SupportEscalation(
            merchant_id=merchant_id,
            customer_id=customer_id,
            conversation_id=conversation_id,
            reason=reason,
            category=category,
            urgency=urgency,
            status="pending"
        )
        session.add(escalation)

        # Update conversation status if provided
        if conversation_id:
            convo_stmt = select(Conversation).where(Conversation.id == conversation_id)
            convo_res = await session.execute(convo_stmt)
            convo = convo_res.scalars().first()
            if convo:
                convo.status = "awaiting_human"

        # Load merchant notification settings
        sett_stmt = select(MerchantSettings).where(MerchantSettings.merchant_id == merchant_id)
        sett_res = await session.execute(sett_stmt)
        settings = sett_res.scalars().first()

        notification_phone = settings.notification_phone if settings else None
        escalation_msg = settings.escalation_message if settings else "Transferring you to our support team."

        await session.flush()

        return {
            "success": True,
            "escalation_id": escalation.id,
            "status": "pending",
            "notified_channel": "whatsapp",
            "staff_contact": notification_phone,
            "customer_message": escalation_msg
        }

    @classmethod
    async def resolve_escalation(
        cls,
        session: AsyncSession,
        escalation_id: str,
        resolution_notes: str,
        resolved_by: str
    ) -> Dict[str, Any]:
        """Mark an escalation as resolved and resume normal AI assistance."""
        stmt = select(SupportEscalation).where(SupportEscalation.id == escalation_id)
        res = await session.execute(stmt)
        esc = res.scalars().first()
        if not esc:
            return {"success": False, "error": f"Escalation {escalation_id} not found."}

        esc.status = "resolved"
        esc.resolution_notes = resolution_notes
        esc.assigned_to = resolved_by

        if esc.conversation_id:
            convo_stmt = select(Conversation).where(Conversation.id == esc.conversation_id)
            convo_res = await session.execute(convo_stmt)
            convo = convo_res.scalars().first()
            if convo:
                convo.status = "active"

        await session.flush()
        return {"success": True, "escalation_id": esc.id, "status": "resolved"}
