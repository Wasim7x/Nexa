import csv
import io
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Response, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from backend.app.core.database import get_db
from backend.app.models.shared import Customer, CustomerMerchantProfile, Message, Conversation, MerchantUser, Merchant
from backend.app.api.deps import get_current_user, get_current_merchant
from backend.app.guardrails.audit_logger import AuditLogger

router = APIRouter(prefix="/customers", tags=["Customers"])

@router.get("")
async def list_customers(
    search: Optional[str] = None,
    opted_in: Optional[bool] = None,
    merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    """List customers with merchant-scoped profile data."""
    stmt = (
        select(CustomerMerchantProfile)
        .options(selectinload(CustomerMerchantProfile.customer))
        .where(CustomerMerchantProfile.merchant_id == merchant.id)
    )

    if opted_in is not None:
        stmt = stmt.where(CustomerMerchantProfile.opt_in_promotions == opted_in)

    res = await db.execute(stmt)
    profiles = res.scalars().all()

    output = []
    for p in profiles:
        c = p.customer
        if search:
            s_lower = search.lower()
            name_match = (c.name and s_lower in c.name.lower()) or (p.preferred_name and s_lower in p.preferred_name.lower())
            phone_match = s_lower in c.whatsapp_phone.lower()
            if not (name_match or phone_match):
                continue

        output.append({
            "customer_id": c.id,
            "whatsapp_phone": c.whatsapp_phone,
            "display_name": p.preferred_name or c.name or "WhatsApp Customer",
            "opt_in_promotions": p.opt_in_promotions,
            "interaction_count": p.interaction_count,
            "last_interaction": p.last_interaction_at.isoformat() if p.last_interaction_at else None,
            "notes": p.notes
        })

    return output

@router.get("/export/csv")
async def export_customers_csv(
    merchant: Merchant = Depends(get_current_merchant),
    current_user: Optional[MerchantUser] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export customer list to CSV with audit logging. Restricted to authorized roles."""
    if current_user and current_user.role not in ["admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: Customer data exports require administrator role."
        )

    stmt = (
        select(CustomerMerchantProfile)
        .options(selectinload(CustomerMerchantProfile.customer))
        .where(CustomerMerchantProfile.merchant_id == merchant.id)
    )
    res = await db.execute(stmt)
    profiles = res.scalars().all()

    # Generate CSV in-memory
    output_str = io.StringIO()
    writer = csv.writer(output_str)
    writer.writerow(["Customer ID", "Phone Number", "Preferred Name", "Interactions", "Opted In", "Last Interaction"])

    for p in profiles:
        c = p.customer
        writer.writerow([
            c.id,
            c.whatsapp_phone,
            p.preferred_name or c.name or "",
            p.interaction_count,
            "Yes" if p.opt_in_promotions else "No",
            p.last_interaction_at.strftime("%Y-%m-%d %H:%M") if p.last_interaction_at else ""
        ])

    # Record Audit Log
    user_id = current_user.id if current_user else "admin"
    await AuditLogger.log_event(
        action="CUSTOMER_DATA_EXPORT_CSV",
        resource_type="customer_export",
        merchant_id=merchant.id,
        user_id=user_id,
        details={"record_count": len(profiles)}
    )

    csv_data = output_str.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=customers_{merchant.slug}.csv"}
    )
