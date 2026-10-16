from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.models.shared import SupportEscalation, Merchant, MerchantUser
from backend.app.services.escalation_service import EscalationService
from backend.app.api.deps import get_current_merchant, get_current_user

router = APIRouter(prefix="/escalations", tags=["Support & Escalations"])

class ResolveEscalationRequest(BaseModel):
    resolution_notes: str

@router.get("")
async def list_escalations(
    status_filter: Optional[str] = None,
    merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    """List customer support escalations for active merchant."""
    stmt = select(SupportEscalation).where(SupportEscalation.merchant_id == merchant.id)
    if status_filter:
        stmt = stmt.where(SupportEscalation.status == status_filter)

    res = await db.execute(stmt)
    escalations = res.scalars().all()

    return [
        {
            "id": e.id,
            "customer_id": e.customer_id,
            "reason": e.reason,
            "category": e.category,
            "urgency": e.urgency,
            "status": e.status,
            "assigned_to": e.assigned_to,
            "resolution_notes": e.resolution_notes,
            "created_at": e.created_at.isoformat()
        }
        for e in escalations
    ]

@router.put("/{escalation_id}/resolve")
async def resolve_escalation(
    escalation_id: str,
    req: ResolveEscalationRequest,
    current_user: MerchantUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark an escalation as resolved and return conversation to AI assistance."""
    res = await EscalationService.resolve_escalation(
        session=db,
        escalation_id=escalation_id,
        resolution_notes=req.resolution_notes,
        resolved_by=current_user.full_name
    )
    if not res.get("success"):
        raise HTTPException(status_code=404, detail=res.get("error"))
    await db.commit()
    return res
