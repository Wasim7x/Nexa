import random
import string
from datetime import date, time, datetime, timedelta
from typing import List, Dict, Any, Optional
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from backend.app.models.dental import DentalService, DentalStaff, DentalAvailability, DentalAppointment
from backend.app.guardrails.authorization import AuthorizationGuardrail

class DentalBusinessService:
    """Business service for SmileCare Dental Clinic operations."""

    @classmethod
    async def list_services(
        cls,
        session: AsyncSession,
        merchant_id: str,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List dental services and consultation fees."""
        stmt = select(DentalService).where(DentalService.merchant_id == merchant_id, DentalService.is_active == True)
        if category:
            stmt = stmt.where(DentalService.category.ilike(f"%{category}%"))

        result = await session.execute(stmt)
        services = result.scalars().all()

        return [
            {
                "service_id": s.id,
                "name": s.name,
                "category": s.category,
                "duration_minutes": s.duration_minutes,
                "consultation_fee": float(s.consultation_fee),
                "description": s.description
            }
            for s in services
        ]

    @classmethod
    async def check_available_slots(
        cls,
        session: AsyncSession,
        merchant_id: str,
        slot_date: Optional[date] = None,
        dentist_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Check open clinic appointment slots."""
        if not slot_date:
            slot_date = date.today() + timedelta(days=1)

        stmt = (
            select(DentalAvailability)
            .options(selectinload(DentalAvailability.dentist))
            .where(
                DentalAvailability.merchant_id == merchant_id,
                DentalAvailability.slot_date == slot_date,
                DentalAvailability.is_booked == False
            )
            .order_by(DentalAvailability.start_time)
        )
        if dentist_id:
            stmt = stmt.where(DentalAvailability.dentist_id == dentist_id)

        result = await session.execute(stmt)
        slots = result.scalars().all()

        return [
            {
                "slot_id": sl.id,
                "date": sl.slot_date.isoformat(),
                "start_time": sl.start_time.strftime("%H:%M"),
                "end_time": sl.end_time.strftime("%H:%M"),
                "dentist_name": sl.dentist.name if sl.dentist else "Attending Dentist",
                "dentist_id": sl.dentist_id
            }
            for sl in slots
        ]

    @classmethod
    async def book_appointment(
        cls,
        session: AsyncSession,
        merchant_id: str,
        customer_id: str,
        service_id: str,
        slot_date: date,
        start_time_val: time,
        dentist_id: Optional[str] = None,
        chief_complaint: Optional[str] = None
    ) -> Dict[str, Any]:
        """Book dental appointment with double-booking prevention."""
        # 1. Verify service
        serv_stmt = select(DentalService).where(DentalService.merchant_id == merchant_id, DentalService.id == service_id)
        serv_res = await session.execute(serv_stmt)
        service = serv_res.scalars().first()
        if not service:
            return {"success": False, "error": f"Dental service {service_id} not found."}

        # 2. Lock available slot
        slot_stmt = select(DentalAvailability).where(
            DentalAvailability.merchant_id == merchant_id,
            DentalAvailability.slot_date == slot_date,
            DentalAvailability.start_time == start_time_val,
            DentalAvailability.is_booked == False
        )
        if dentist_id:
            slot_stmt = slot_stmt.where(DentalAvailability.dentist_id == dentist_id)

        slot_res = await session.execute(slot_stmt)
        slot = slot_res.scalars().first()

        if not slot:
            return {
                "success": False,
                "error": f"Requested slot at {start_time_val.strftime('%H:%M')} on {slot_date.isoformat()} is not available or already booked."
            }

        slot.is_booked = True
        actual_dentist_id = slot.dentist_id

        calc_end = (datetime.combine(slot_date, start_time_val) + timedelta(minutes=service.duration_minutes)).time()
        booking_ref = f"DNT-{''.join(random.choices(string.digits, k=6))}"

        appointment = DentalAppointment(
            booking_reference=booking_ref,
            merchant_id=merchant_id,
            customer_id=customer_id,
            service_id=service.id,
            dentist_id=actual_dentist_id,
            appointment_date=slot_date,
            start_time=start_time_val,
            end_time=calc_end,
            status="confirmed",
            chief_complaint=chief_complaint
        )
        session.add(appointment)
        await session.flush()

        dentist_name = "Dentist"
        if actual_dentist_id:
            d_stmt = select(DentalStaff).where(DentalStaff.id == actual_dentist_id)
            d_res = await session.execute(d_stmt)
            d_obj = d_res.scalars().first()
            if d_obj:
                dentist_name = d_obj.name

        return {
            "success": True,
            "booking_reference": appointment.booking_reference,
            "service_name": service.name,
            "dentist_name": dentist_name,
            "appointment_date": slot_date.isoformat(),
            "start_time": start_time_val.strftime("%H:%M"),
            "end_time": calc_end.strftime("%H:%M"),
            "consultation_fee": float(service.consultation_fee),
            "status": "confirmed"
        }

    @classmethod
    async def get_appointment(
        cls,
        session: AsyncSession,
        merchant_id: str,
        customer_id: str,
        booking_reference: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve dental appointment with customer ownership check."""
        stmt = (
            select(DentalAppointment)
            .options(selectinload(DentalAppointment.service), selectinload(DentalAppointment.dentist))
            .where(
                DentalAppointment.merchant_id == merchant_id,
                DentalAppointment.booking_reference == booking_reference
            )
        )
        result = await session.execute(stmt)
        appt = result.scalars().first()
        if not appt:
            return None

        if not AuthorizationGuardrail.verify_customer_ownership(appt.customer_id, customer_id):
            raise PermissionError("Access denied: You do not own this appointment record.")

        return {
            "booking_reference": appt.booking_reference,
            "service_name": appt.service.name if appt.service else "Service",
            "dentist_name": appt.dentist.name if appt.dentist else "Dentist",
            "date": appt.appointment_date.isoformat(),
            "time": appt.start_time.strftime("%H:%M"),
            "status": appt.status,
            "chief_complaint": appt.chief_complaint
        }

    @classmethod
    async def cancel_appointment(
        cls,
        session: AsyncSession,
        merchant_id: str,
        customer_id: str,
        booking_reference: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Cancel dental appointment and free the clinical chair slot."""
        stmt = select(DentalAppointment).where(
            DentalAppointment.merchant_id == merchant_id,
            DentalAppointment.booking_reference == booking_reference
        )
        result = await session.execute(stmt)
        appt = result.scalars().first()
        if not appt:
            return {"success": False, "error": f"Appointment {booking_reference} not found."}

        if not AuthorizationGuardrail.verify_customer_ownership(appt.customer_id, customer_id):
            raise PermissionError("Access denied: You cannot cancel another customer's appointment.")

        if appt.status == "cancelled":
            return {"success": False, "error": "Appointment is already cancelled."}

        # Release slot
        slot_stmt = select(DentalAvailability).where(
            DentalAvailability.merchant_id == merchant_id,
            DentalAvailability.slot_date == appt.appointment_date,
            DentalAvailability.start_time == appt.start_time
        )
        slot_res = await session.execute(slot_stmt)
        slot = slot_res.scalars().first()
        if slot:
            slot.is_booked = False

        appt.status = "cancelled"
        appt.cancellation_reason = reason
        await session.flush()

        return {
            "success": True,
            "booking_reference": appt.booking_reference,
            "status": "cancelled",
            "message": "Dental appointment successfully cancelled."
        }
