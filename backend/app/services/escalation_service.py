from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.models.shared import SupportEscalation, Conversation, MerchantSettings, Merchant, Customer
from backend.app.whatsapp.client import WhatsAppCloudClient

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
        """Create a support escalation and update conversation state to awaiting_human, deduplicating active requests."""
        # 1. Deduplication check: return existing pending escalation if one is already active
        existing_stmt = select(SupportEscalation).where(
            SupportEscalation.merchant_id == merchant_id,
            SupportEscalation.customer_id == customer_id,
            SupportEscalation.status == "pending"
        )
        if conversation_id:
            existing_stmt = existing_stmt.where(SupportEscalation.conversation_id == conversation_id)
        existing = (await session.execute(existing_stmt)).scalars().first()

        if existing:
            sett_stmt = select(MerchantSettings).where(MerchantSettings.merchant_id == merchant_id)
            settings = (await session.execute(sett_stmt)).scalars().first()
            notification_phone = (settings.notification_phone if settings and settings.notification_phone else "9351489260")
            escalation_msg = settings.escalation_message if settings and settings.escalation_message else "Your request has already been escalated to our human support team. An assistant will be with you shortly."
            return {
                "success": True,
                "escalation_id": existing.id,
                "status": "pending",
                "notified_channel": "whatsapp",
                "staff_contact": notification_phone,
                "customer_message": escalation_msg,
                "is_duplicate": True
            }

        # 2. Create new escalation record
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

        # 3. Update conversation status if provided
        if conversation_id:
            convo_stmt = select(Conversation).where(Conversation.id == conversation_id)
            convo_res = await session.execute(convo_stmt)
            convo = convo_res.scalars().first()
            if convo:
                convo.status = "awaiting_human"

        # 4. Load merchant notification settings
        sett_stmt = select(MerchantSettings).where(MerchantSettings.merchant_id == merchant_id)
        sett_res = await session.execute(sett_stmt)
        settings = sett_res.scalars().first()

        # Configured human assistant phone (Requirement 3: 9351489260)
        notification_phone = settings.notification_phone if settings and settings.notification_phone else "9351489260"
        escalation_msg = settings.escalation_message if settings and settings.escalation_message else "I am connecting you with our human assistant team for assistance."

        # 5. Look up customer phone for notification details
        cust_phone = "Customer"
        cust_stmt = select(Customer).where(Customer.id == customer_id)
        cust = (await session.execute(cust_stmt)).scalars().first()
        if cust and cust.whatsapp_phone:
            cust_phone = cust.whatsapp_phone

        # 6. Record outbound notification for human assistant
        await WhatsAppCloudClient.send_text_message(
            recipient_phone=notification_phone,
            message_text=f"🚨 [Nexa Escalation Alert]\nMerchant: {merchant_id}\nCustomer: {cust_phone}\nUrgency: {urgency.upper()}\nReason: {reason}"
        )

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
        resolved_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Mark an escalation as resolved and resume normal AI assistance."""
        stmt = select(SupportEscalation).where(SupportEscalation.id == escalation_id)
        res = await session.execute(stmt)
        esc = res.scalars().first()
        if not esc:
            return {"success": False, "error": f"Escalation {escalation_id} not found."}

        esc.status = "resolved"
        esc.resolution_notes = resolution_notes
        esc.assigned_to = resolved_by or "Human Assistant (9351489260)"

        if esc.conversation_id:
            convo_stmt = select(Conversation).where(Conversation.id == esc.conversation_id)
            convo_res = await session.execute(convo_stmt)
            convo = convo_res.scalars().first()
            if convo:
                convo.status = "active"

        await session.flush()
        return {"success": True, "escalation_id": esc.id, "status": "resolved"}
