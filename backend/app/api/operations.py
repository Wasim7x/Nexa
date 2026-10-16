from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.app.core.database import get_db
from backend.app.models.shared import Merchant, Customer
from backend.app.models.grocery import GroceryOrder
from backend.app.models.sweets import SweetsOrder
from backend.app.models.salon import SalonAppointment
from backend.app.models.dental import DentalAppointment
from backend.app.api.deps import get_current_merchant
from backend.app.guardrails.audit_logger import AuditLogger

router = APIRouter(prefix="/operations", tags=["Orders & Appointments"])

class StatusUpdateRequest(BaseModel):
    status: str
    reason: Optional[str] = None

@router.get("/records")
async def list_operations_records(
    status_filter: Optional[str] = None,
    merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    """List orders or appointments for the active merchant."""
    m_id = merchant.id
    b_type = merchant.business_type

    if b_type == "grocery":
        stmt = select(GroceryOrder).options(selectinload(GroceryOrder.items)).where(GroceryOrder.merchant_id == m_id)
        if status_filter:
            stmt = stmt.where(GroceryOrder.status == status_filter)
        orders = (await db.execute(stmt)).scalars().all()
        return [
            {
                "id": o.id,
                "reference": o.order_number,
                "type": "order",
                "status": o.status,
                "total": float(o.total_amount),
                "created_at": o.created_at.isoformat(),
                "delivery_address": o.delivery_address,
                "items_count": len(o.items)
            }
            for o in orders
        ]

    elif b_type == "sweets":
        stmt = select(SweetsOrder).options(selectinload(SweetsOrder.items)).where(SweetsOrder.merchant_id == m_id)
        if status_filter:
            stmt = stmt.where(SweetsOrder.status == status_filter)
        orders = (await db.execute(stmt)).scalars().all()
        return [
            {
                "id": o.id,
                "reference": o.order_number,
                "type": "order",
                "status": o.status,
                "order_type": o.order_type,
                "total": float(o.total_amount),
                "created_at": o.created_at.isoformat(),
                "gift_packaging": o.gift_packaging,
                "items_count": len(o.items)
            }
            for o in orders
        ]

    elif b_type == "salon":
        stmt = select(SalonAppointment).options(
            selectinload(SalonAppointment.service),
            selectinload(SalonAppointment.staff)
        ).where(SalonAppointment.merchant_id == m_id)
        if status_filter:
            stmt = stmt.where(SalonAppointment.status == status_filter)
        appts = (await db.execute(stmt)).scalars().all()
        return [
            {
                "id": a.id,
                "reference": a.booking_reference,
                "type": "appointment",
                "service_name": a.service.name if a.service else "Service",
                "staff_name": a.staff.name if a.staff else "Stylist",
                "date": a.appointment_date.isoformat(),
                "time": a.start_time.strftime("%H:%M"),
                "status": a.status,
                "created_at": a.created_at.isoformat()
            }
            for a in appts
        ]

    elif b_type == "dental":
        stmt = select(DentalAppointment).options(
            selectinload(DentalAppointment.service),
            selectinload(DentalAppointment.dentist)
        ).where(DentalAppointment.merchant_id == m_id)
        if status_filter:
            stmt = stmt.where(DentalAppointment.status == status_filter)
        appts = (await db.execute(stmt)).scalars().all()
        return [
            {
                "id": a.id,
                "reference": a.booking_reference,
                "type": "appointment",
                "service_name": a.service.name if a.service else "Dental Service",
                "dentist_name": a.dentist.name if a.dentist else "Dentist",
                "date": a.appointment_date.isoformat(),
                "time": a.start_time.strftime("%H:%M"),
                "status": a.status,
                "chief_complaint": a.chief_complaint,
                "created_at": a.created_at.isoformat()
            }
            for a in appts
        ]
    return []

@router.put("/records/{reference}/status")
async def update_record_status(
    reference: str,
    req: StatusUpdateRequest,
    merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    """Update order or appointment status (e.g. delivered, completed, cancelled)."""
    m_id = merchant.id
    b_type = merchant.business_type

    if b_type == "grocery":
        stmt = select(GroceryOrder).where(GroceryOrder.merchant_id == m_id, GroceryOrder.order_number == reference)
        order = (await db.execute(stmt)).scalars().first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        order.status = req.status
        await db.commit()
        return {"reference": reference, "status": order.status}

    elif b_type == "sweets":
        stmt = select(SweetsOrder).where(SweetsOrder.merchant_id == m_id, SweetsOrder.order_number == reference)
        order = (await db.execute(stmt)).scalars().first()
        if not order:
            raise HTTPException(status_code=404, detail="Sweets order not found")
        order.status = req.status
        await db.commit()
        return {"reference": reference, "status": order.status}

    elif b_type == "salon":
        stmt = select(SalonAppointment).where(SalonAppointment.merchant_id == m_id, SalonAppointment.booking_reference == reference)
        appt = (await db.execute(stmt)).scalars().first()
        if not appt:
            raise HTTPException(status_code=404, detail="Appointment not found")
        appt.status = req.status
        await db.commit()
        return {"reference": reference, "status": appt.status}

    elif b_type == "dental":
        stmt = select(DentalAppointment).where(DentalAppointment.merchant_id == m_id, DentalAppointment.booking_reference == reference)
        appt = (await db.execute(stmt)).scalars().first()
        if not appt:
            raise HTTPException(status_code=404, detail="Dental appointment not found")
        appt.status = req.status
        await db.commit()
        return {"reference": reference, "status": appt.status}

    raise HTTPException(status_code=400, detail="Invalid merchant type")
