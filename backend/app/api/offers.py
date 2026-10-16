from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.models.shared import KnowledgeDocument, Merchant, CustomerMerchantProfile, NotificationJob
from backend.app.notifications.templates import NotificationTemplates
from backend.app.notifications.service import NotificationService
from backend.app.api.deps import get_current_merchant
from backend.app.guardrails.audit_logger import AuditLogger

router = APIRouter(prefix="/offers", tags=["Offers & Campaigns"])

class OfferCreateRequest(BaseModel):
    title: str
    details: str
    target_category: Optional[str] = None
    schedule_broadcast: bool = False

@router.get("")
async def list_offers(
    merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    """List active merchant promotional offers."""
    stmt = select(KnowledgeDocument).where(
        KnowledgeDocument.merchant_id == merchant.id,
        KnowledgeDocument.doc_type == "offer"
    )
    res = await db.execute(stmt)
    docs = res.scalars().all()
    return [
        {
            "id": d.id,
            "title": d.title,
            "details": d.content,
            "is_published": d.is_published,
            "created_at": d.created_at.isoformat()
        }
        for d in docs
    ]

@router.post("")
async def create_offer(
    req: OfferCreateRequest,
    merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    """Create offer and optionally schedule notification campaign to opted-in customers."""
    doc = KnowledgeDocument(
        merchant_id=merchant.id,
        title=req.title,
        doc_type="offer",
        content=req.details,
        embedding_status="indexed",
        is_published=True
    )
    db.add(doc)
    await db.flush()

    dispatched_count = 0
    if req.schedule_broadcast:
        # Find all opted-in customers for this merchant
        prof_stmt = select(CustomerMerchantProfile).where(
            CustomerMerchantProfile.merchant_id == merchant.id,
            CustomerMerchantProfile.opt_in_promotions == True
        )
        profiles = (await db.execute(prof_stmt)).scalars().all()

        for prof in profiles:
            job = await NotificationService.queue_notification(
                session=db,
                merchant_id=merchant.id,
                customer_id=prof.customer_id,
                event_type="offer.campaign_due",
                payload={"title": req.title, "details": req.details},
                idempotency_key=f"offer_{doc.id}_{prof.customer_id}"
            )
            await NotificationService.dispatch_notification(db, job.id)
            dispatched_count += 1

    await db.commit()

    return {
        "id": doc.id,
        "title": doc.title,
        "is_published": True,
        "campaign_dispatched_count": dispatched_count,
        "message_preview": NotificationTemplates.render_promotional_campaign(merchant.name, req.title, req.details)
    }

@router.post("/preview")
async def preview_campaign(
    req: OfferCreateRequest,
    merchant: Merchant = Depends(get_current_merchant)
):
    """Generate realistic WhatsApp message preview and estimate eligible audience."""
    return {
        "formatted_whatsapp_message": NotificationTemplates.render_promotional_campaign(
            merchant.name, req.title, req.details
        ),
        "target_audience": "Opted-in customers with verified WhatsApp numbers"
    }
