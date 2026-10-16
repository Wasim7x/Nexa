import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.core.database import AsyncSessionLocal
from backend.app.models.shared import NotificationJob, NotificationEvent, Customer, Merchant, CustomerMerchantProfile
from backend.app.whatsapp.client import WhatsAppCloudClient
from backend.app.notifications.templates import NotificationTemplates

logger = logging.getLogger("vera.notifications")

class NotificationService:
    """Manages transactional and event-driven WhatsApp customer notifications."""

    @classmethod
    async def queue_notification(
        cls,
        session: AsyncSession,
        merchant_id: str,
        customer_id: str,
        event_type: str,
        payload: Dict[str, Any],
        idempotency_key: Optional[str] = None
    ) -> NotificationJob:
        """
        Creates and queues a notification job with idempotency protection.
        """
        if idempotency_key:
            stmt = select(NotificationJob).where(NotificationJob.idempotency_key == idempotency_key)
            existing = (await session.execute(stmt)).scalars().first()
            if existing:
                logger.info(f"Duplicate notification ignored with idempotency key {idempotency_key}")
                return existing

        job = NotificationJob(
            merchant_id=merchant_id,
            customer_id=customer_id,
            event_type=event_type,
            status="pending",
            payload_json=payload,
            idempotency_key=idempotency_key,
            scheduled_at=datetime.now(timezone.utc)
        )
        session.add(job)
        await session.flush()
        return job

    @classmethod
    async def dispatch_notification(
        cls,
        session: AsyncSession,
        job_id: str
    ) -> Dict[str, Any]:
        """Dispatch a single queued notification job via WhatsApp."""
        stmt = select(NotificationJob).where(NotificationJob.id == job_id)
        res = await session.execute(stmt)
        job = res.scalars().first()
        if not job or job.status == "sent":
            return {"status": "skipped"}

        # Load customer
        cust_stmt = select(Customer).where(Customer.id == job.customer_id)
        cust = (await session.execute(cust_stmt)).scalars().first()
        if not cust or not cust.whatsapp_phone:
            job.status = "failed"
            await session.commit()
            return {"status": "failed", "error": "Customer has no WhatsApp phone number"}

        # Load merchant
        merch_stmt = select(Merchant).where(Merchant.id == job.merchant_id)
        merchant = (await session.execute(merch_stmt)).scalars().first()
        merch_name = merchant.name if merchant else "Merchant"

        # Check promotional opt-out
        payload = job.payload_json or {}
        if job.event_type.startswith("offer."):
            prof_stmt = select(CustomerMerchantProfile).where(
                CustomerMerchantProfile.customer_id == job.customer_id,
                CustomerMerchantProfile.merchant_id == job.merchant_id
            )
            prof = (await session.execute(prof_stmt)).scalars().first()
            if prof and not prof.opt_in_promotions:
                job.status = "cancelled"
                await session.commit()
                return {"status": "cancelled", "reason": "Customer opted out of promotional messages"}

        # Format message based on event type
        msg_text = ""
        if job.event_type == "order.created":
            msg_text = NotificationTemplates.render_order_confirmation(
                merch_name, payload.get("order_number", ""), payload.get("total_amount", 0.0)
            )
        elif job.event_type == "order.status_changed":
            msg_text = NotificationTemplates.render_order_status_update(
                merch_name, payload.get("order_number", ""), payload.get("new_status", "")
            )
        elif job.event_type == "order.cancelled":
            msg_text = NotificationTemplates.render_order_cancelled(
                merch_name, payload.get("order_number", "")
            )
        elif job.event_type == "appointment.booked":
            msg_text = NotificationTemplates.render_appointment_confirmation(
                merch_name, payload.get("service_name", ""), payload.get("date", ""),
                payload.get("time", ""), payload.get("booking_reference", "")
            )
        elif job.event_type == "appointment.reminder_due":
            msg_text = NotificationTemplates.render_appointment_reminder(
                merch_name, payload.get("service_name", ""), payload.get("time", ""),
                payload.get("booking_reference", "")
            )
        elif job.event_type == "offer.campaign_due":
            msg_text = NotificationTemplates.render_promotional_campaign(
                merch_name, payload.get("title", ""), payload.get("details", "")
            )
        else:
            msg_text = payload.get("text", f"Notification from {merch_name}")

        # Send via WhatsApp client
        send_res = await WhatsAppCloudClient.send_text_message(cust.whatsapp_phone, msg_text)
        is_success = "error" not in send_res

        job.status = "sent" if is_success else "failed"

        # Record event
        event = NotificationEvent(
            job_id=job.id,
            merchant_id=job.merchant_id,
            event_type=job.event_type,
            status=job.status,
            provider_response=send_res
        )
        session.add(event)
        await session.commit()

        return {"status": job.status, "provider_response": send_res}
