from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.app.core.database import get_db
from backend.app.models.shared import (
    Merchant, CustomerMerchantProfile, Conversation, SupportEscalation,
    KnowledgeDocument, NotificationJob
)
from backend.app.models.grocery import GroceryOrder
from backend.app.models.sweets import SweetsOrder
from backend.app.models.salon import SalonAppointment
from backend.app.models.dental import DentalAppointment
from backend.app.api.deps import get_current_user, get_current_merchant

router = APIRouter(prefix="", tags=["Dashboard & Merchants"])

@router.get("/merchants")
async def list_merchants(db: AsyncSession = Depends(get_db)):
    """List all supported merchants."""
    stmt = select(Merchant).where(Merchant.is_active == True)
    res = await db.execute(stmt)
    merchants = res.scalars().all()
    return [
        {
            "id": m.id,
            "name": m.name,
            "slug": m.slug,
            "business_type": m.business_type,
            "phone_number": m.phone_number,
            "description": m.description
        }
        for m in merchants
    ]

@router.get("/dashboard/stats")
async def get_dashboard_stats(
    merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    """Aggregate live KPI metrics scoped strictly to authorized merchant."""
    merchant_id = merchant.id

    # 1. Customer count
    cust_stmt = select(func.count(CustomerMerchantProfile.id)).where(CustomerMerchantProfile.merchant_id == merchant_id)
    cust_count = (await db.execute(cust_stmt)).scalar() or 0

    # 2. Conversations count
    convo_stmt = select(func.count(Conversation.id)).where(Conversation.active_merchant_id == merchant_id)
    convo_count = (await db.execute(convo_stmt)).scalar() or 0

    # 3. Open escalations count
    esc_stmt = select(func.count(SupportEscalation.id)).where(
        SupportEscalation.merchant_id == merchant_id,
        SupportEscalation.status == "pending"
    )
    esc_count = (await db.execute(esc_stmt)).scalar() or 0

    # 4. Published Knowledge Documents count
    kb_stmt = select(func.count(KnowledgeDocument.id)).where(
        KnowledgeDocument.merchant_id == merchant_id,
        KnowledgeDocument.is_published == True
    )
    kb_count = (await db.execute(kb_stmt)).scalar() or 0

    # 5. Orders or Appointments count & total revenue
    orders_count = 0
    total_revenue = 0.0

    if merchant.business_type == "grocery":
        g_stmt = select(func.count(GroceryOrder.id), func.sum(GroceryOrder.total_amount)).where(GroceryOrder.merchant_id == merchant_id)
        g_res = (await db.execute(g_stmt)).first()
        orders_count = g_res[0] or 0
        total_revenue = float(g_res[1] or 0.0)

    elif merchant.business_type == "sweets":
        s_stmt = select(func.count(SweetsOrder.id), func.sum(SweetsOrder.total_amount)).where(SweetsOrder.merchant_id == merchant_id)
        s_res = (await db.execute(s_stmt)).first()
        orders_count = s_res[0] or 0
        total_revenue = float(s_res[1] or 0.0)

    elif merchant.business_type == "salon":
        sln_stmt = select(func.count(SalonAppointment.id)).where(SalonAppointment.merchant_id == merchant_id)
        orders_count = (await db.execute(sln_stmt)).scalar() or 0
        total_revenue = orders_count * 65.0  # Avg ticket

    elif merchant.business_type == "dental":
        dnt_stmt = select(func.count(DentalAppointment.id)).where(DentalAppointment.merchant_id == merchant_id)
        orders_count = (await db.execute(dnt_stmt)).scalar() or 0
        total_revenue = orders_count * 120.0  # Avg fee

    # 6. Notifications stats
    notif_stmt = select(func.count(NotificationJob.id)).where(NotificationJob.merchant_id == merchant_id)
    notif_count = (await db.execute(notif_stmt)).scalar() or 0

    return {
        "merchant": {
            "id": merchant.id,
            "name": merchant.name,
            "business_type": merchant.business_type
        },
        "customers_count": cust_count,
        "conversations_count": convo_count,
        "orders_or_appointments_count": orders_count,
        "total_revenue": total_revenue,
        "pending_escalations": esc_count,
        "knowledge_docs_count": kb_count,
        "notifications_count": notif_count
    }
