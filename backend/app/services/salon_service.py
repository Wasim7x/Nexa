import random
import string
from datetime import date, time, datetime, timedelta
from typing import List, Dict, Any, Optional
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from backend.app.models.salon import SalonService, SalonStaff, SalonAvailability, SalonAppointment
from backend.app.guardrails.authorization import AuthorizationGuardrail

class SalonBusinessService:
    """Business service for Glow & Glamour Salon operations."""

    @classmethod
    async def list_services(
        cls,
        session: AsyncSession,
        merchant_id: str,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List active salon treatments, duration, and prices."""
        stmt = select(SalonService).where(SalonService.merchant_id == merchant_id, SalonService.is_active == True)
        if category:
            stmt = stmt.where(SalonService.category.ilike(f"%{category}%"))

        result = await session.execute(stmt)
        services = result.scalars().all()

        return [
            {
                "service_id": s.id,
                "name": s.name,
                "category": s.category,
                "duration_minutes": s.duration_minutes,
                "price": float(s.price),
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
        staff_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Check open appointment slots."""
        if not slot_date:
            slot_date = date.today() + timedelta(days=1)

        stmt = (
            select(SalonAvailability)
            .options(selectinload(SalonAvailability.staff))
            .where(
                SalonAvailability.merchant_id == merchant_id,
                SalonAvailability.slot_date == slot_date,
                SalonAvailability.is_booked == False
            )
            .order_by(SalonAvailability.start_time)
        )
        if staff_id:
            stmt = stmt.where(SalonAvailability.staff_id == staff_id)

        result = await session.execute(stmt)
        slots = result.scalars().all()

        return [
            {
                "slot_id": sl.id,
                "date": sl.slot_date.isoformat(),
                "start_time": sl.start_time.strftime("%H:%M"),
                "end_time": sl.end_time.strftime("%H:%M"),
                "staff_name": sl.staff.name if sl.staff else "Any available stylist",
                "staff_id": sl.staff_id
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
        staff_id: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Book salon appointment transactionally with double-booking prevention.
        """
        # 1. Verify service
        serv_stmt = select(SalonService).where(SalonService.merchant_id == merchant_id, SalonService.id == service_id)
        serv_res = await session.execute(serv_stmt)
        service = serv_res.scalars().first()
        if not service:
            return {"success": False, "error": f"Salon service {service_id} not found."}

        # 2. Find and lock the availability slot
        slot_stmt = select(SalonAvailability).where(
            SalonAvailability.merchant_id == merchant_id,
            SalonAvailability.slot_date == slot_date,
            SalonAvailability.start_time == start_time_val,
            SalonAvailability.is_booked == False
        )
        if staff_id:
            slot_stmt = slot_stmt.where(SalonAvailability.staff_id == staff_id)

        slot_res = await session.execute(slot_stmt)
        slot = slot_res.scalars().first()

        if not slot:
            return {
                "success": False,
                "error": f"Requested slot at {start_time_val.strftime('%H:%M')} on {slot_date.isoformat()} is not available or already booked."
            }

        # Mark slot as booked
        slot.is_booked = True
        actual_staff_id = slot.staff_id

        # Calculate end time based on service duration
        calc_end = (datetime.combine(slot_date, start_time_val) + timedelta(minutes=service.duration_minutes)).time()

        booking_ref = f"SLN-{''.join(random.choices(string.digits, k=6))}"

        appointment = SalonAppointment(
            booking_reference=booking_ref,
            merchant_id=merchant_id,
            customer_id=customer_id,
            service_id=service.id,
            staff_id=actual_staff_id,
            appointment_date=slot_date,
            start_time=start_time_val,
            end_time=calc_end,
            status="confirmed",
            notes=notes
        )
        session.add(appointment)
        await session.flush()

        # Load staff name
        staff_name = "Stylist"
        if actual_staff_id:
            staff_stmt = select(SalonStaff).where(SalonStaff.id == actual_staff_id)
            st_res = await session.execute(staff_stmt)
            st_obj = st_res.scalars().first()
            if st_obj:
                staff_name = st_obj.name

        return {
            "success": True,
            "booking_reference": appointment.booking_reference,
            "service_name": service.name,
            "staff_name": staff_name,
            "appointment_date": slot_date.isoformat(),
            "start_time": start_time_val.strftime("%H:%M"),
            "end_time": calc_end.strftime("%H:%M"),
            "price": float(service.price),
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
        """Retrieve salon appointment with customer ownership validation."""
        stmt = (
            select(SalonAppointment)
            .options(selectinload(SalonAppointment.service), selectinload(SalonAppointment.staff))
            .where(
                SalonAppointment.merchant_id == merchant_id,
                SalonAppointment.booking_reference == booking_reference
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
            "staff_name": appt.staff.name if appt.staff else "Stylist",
            "date": appt.appointment_date.isoformat(),
            "time": appt.start_time.strftime("%H:%M"),
            "status": appt.status,
            "notes": appt.notes
        }

    @classmethod
    async def reschedule_appointment(
        cls,
        session: AsyncSession,
        merchant_id: str,
        customer_id: str,
        booking_reference: str,
        new_slot_date: date,
        new_start_time: time
    ) -> Dict[str, Any]:
        """Reschedule appointment to a new open slot."""
        stmt = select(SalonAppointment).where(
            SalonAppointment.merchant_id == merchant_id,
            SalonAppointment.booking_reference == booking_reference
        )
        result = await session.execute(stmt)
        appt = result.scalars().first()
        if not appt:
            return {"success": False, "error": f"Appointment {booking_reference} not found."}

        if not AuthorizationGuardrail.verify_customer_ownership(appt.customer_id, customer_id):
            raise PermissionError("Access denied: You cannot reschedule another customer's appointment.")

        if appt.status == "cancelled":
            return {"success": False, "error": "Cancelled appointment cannot be rescheduled. Please book a new one."}

        # Check new slot
        new_slot_stmt = select(SalonAvailability).where(
            SalonAvailability.merchant_id == merchant_id,
            SalonAvailability.slot_date == new_slot_date,
            SalonAvailability.start_time == new_start_time,
            SalonAvailability.is_booked == False
        )
        new_slot_res = await session.execute(new_slot_stmt)
        new_slot = new_slot_res.scalars().first()
        if not new_slot:
            return {"success": False, "error": f"No available slot on {new_slot_date} at {new_start_time.strftime('%H:%M')}."}

        # Free previous slot if exists
        old_slot_stmt = select(SalonAvailability).where(
            SalonAvailability.merchant_id == merchant_id,
            SalonAvailability.slot_date == appt.appointment_date,
            SalonAvailability.start_time == appt.start_time
        )
        old_slot_res = await session.execute(old_slot_stmt)
        old_slot = old_slot_res.scalars().first()
        if old_slot:
            old_slot.is_booked = False

        # Book new slot
        new_slot.is_booked = True
        appt.appointment_date = new_slot_date
        appt.start_time = new_start_time
        appt.status = "confirmed"
        await session.flush()

        return {
            "success": True,
            "booking_reference": appt.booking_reference,
            "new_date": new_slot_date.isoformat(),
            "new_time": new_start_time.strftime("%H:%M"),
            "status": "confirmed",
            "message": f"Appointment successfully rescheduled to {new_slot_date} at {new_start_time.strftime('%H:%M')}."
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
        """Cancel salon appointment and release the slot."""
        stmt = select(SalonAppointment).where(
            SalonAppointment.merchant_id == merchant_id,
            SalonAppointment.booking_reference == booking_reference
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
        slot_stmt = select(SalonAvailability).where(
            SalonAvailability.merchant_id == merchant_id,
            SalonAvailability.slot_date == appt.appointment_date,
            SalonAvailability.start_time == appt.start_time
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
            "message": "Salon appointment successfully cancelled."
        }
