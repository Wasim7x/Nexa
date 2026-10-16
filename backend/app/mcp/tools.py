from datetime import date, time
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.mcp.context import MCPCallContext
from backend.app.services.grocery_service import GroceryService
from backend.app.services.sweets_service import SweetsService
from backend.app.services.salon_service import SalonBusinessService
from backend.app.services.dental_service import DentalBusinessService
from backend.app.services.escalation_service import EscalationService
from backend.app.services.customer_service import CustomerService
from backend.app.guardrails.audit_logger import AuditLogger

class MCPBusinessTools:
    """
    Exposes validated MCP business tools to LangGraph and AI agents.
    All calls enforce merchant scope and customer ownership from MCPCallContext.
    """

    # -------------------------------------------------------------------------
    # PRODUCT & ORDER TOOLS
    # -------------------------------------------------------------------------
    @classmethod
    async def search_products(
        cls,
        session: AsyncSession,
        ctx: MCPCallContext,
        query: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search products or items for the active merchant."""
        if ctx.merchant_id == "grocery-store":
            return await GroceryService.search_products(session, ctx.merchant_id, query, category)
        elif ctx.merchant_id == "sweets-shop":
            return await SweetsService.search_products(session, ctx.merchant_id, query, category)
        elif ctx.merchant_id == "glow-salon":
            return await SalonBusinessService.list_services(session, ctx.merchant_id, category)
        elif ctx.merchant_id == "dental-clinic":
            return await DentalBusinessService.list_services(session, ctx.merchant_id, category)
        return []

    @classmethod
    async def check_inventory(
        cls,
        session: AsyncSession,
        ctx: MCPCallContext,
        product_id: str
    ) -> Dict[str, Any]:
        """Check live authoritative inventory for a product."""
        if ctx.merchant_id == "grocery-store":
            details = await GroceryService.get_product_details(session, ctx.merchant_id, product_id)
            return details or {"error": "Product not found"}
        elif ctx.merchant_id == "sweets-shop":
            details = await SweetsService.get_product_details(session, ctx.merchant_id, product_id)
            return details or {"error": "Sweet product not found"}
        return {"error": f"Inventory check is not applicable for {ctx.merchant_id}"}

    @classmethod
    async def get_product_price(
        cls,
        session: AsyncSession,
        ctx: MCPCallContext,
        product_id: str
    ) -> Dict[str, Any]:
        """Get verified current price for a product or service."""
        return await cls.check_inventory(session, ctx, product_id)

    @classmethod
    async def get_active_offers(
        cls,
        session: AsyncSession,
        ctx: MCPCallContext
    ) -> List[Dict[str, Any]]:
        """Get published promotions, discounts, and active offers."""
        if ctx.merchant_id == "grocery-store":
            return await GroceryService.get_active_offers(session, ctx.merchant_id)
        elif ctx.merchant_id == "sweets-shop":
            return await SweetsService.get_active_offers(session, ctx.merchant_id)
        return []

    @classmethod
    async def create_order(
        cls,
        session: AsyncSession,
        ctx: MCPCallContext,
        items: List[Dict[str, Any]],
        delivery_address: Optional[str] = None,
        notes: Optional[str] = None,
        order_type: str = "delivery",
        gift_packaging: bool = False,
        gift_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Place an authoritative order transactionally."""
        if ctx.merchant_id == "grocery-store":
            res = await GroceryService.create_order(
                session=session,
                merchant_id=ctx.merchant_id,
                customer_id=ctx.customer_id,
                items=items,
                delivery_address=delivery_address,
                notes=notes
            )
        elif ctx.merchant_id == "sweets-shop":
            res = await SweetsService.create_order(
                session=session,
                merchant_id=ctx.merchant_id,
                customer_id=ctx.customer_id,
                items=items,
                order_type=order_type,
                delivery_address=delivery_address,
                gift_packaging=gift_packaging,
                gift_message=gift_message
            )
        else:
            return {"success": False, "error": f"Orders are not supported for merchant {ctx.merchant_id}"}

        # Log audit record
        if res.get("success"):
            await AuditLogger.log_event(
                action="ORDER_CREATED",
                resource_type="order",
                merchant_id=ctx.merchant_id,
                customer_phone=ctx.customer_phone,
                resource_id=res.get("order_number"),
                details=res
            )
        return res

    @classmethod
    async def get_order(
        cls,
        session: AsyncSession,
        ctx: MCPCallContext,
        order_number: str
    ) -> Dict[str, Any]:
        """Retrieve order details for the caller."""
        if ctx.merchant_id == "grocery-store":
            order = await GroceryService.get_order(session, ctx.merchant_id, ctx.customer_id, order_number)
        elif ctx.merchant_id == "sweets-shop":
            order = await SweetsService.get_order(session, ctx.merchant_id, ctx.customer_id, order_number)
        else:
            return {"error": "Invalid merchant"}

        if not order:
            return {"error": f"Order {order_number} not found"}
        return order

    @classmethod
    async def cancel_order(
        cls,
        session: AsyncSession,
        ctx: MCPCallContext,
        order_number: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Cancel an order owned by the caller."""
        if ctx.merchant_id == "grocery-store":
            res = await GroceryService.cancel_order(session, ctx.merchant_id, ctx.customer_id, order_number, reason)
        elif ctx.merchant_id == "sweets-shop":
            res = await SweetsService.cancel_order(session, ctx.merchant_id, ctx.customer_id, order_number, reason)
        else:
            return {"success": False, "error": "Orders not supported"}

        if res.get("success"):
            await AuditLogger.log_event(
                action="ORDER_CANCELLED",
                resource_type="order",
                merchant_id=ctx.merchant_id,
                customer_phone=ctx.customer_phone,
                resource_id=order_number,
                details={"reason": reason}
            )
        return res

    # -------------------------------------------------------------------------
    # APPOINTMENT TOOLS
    # -------------------------------------------------------------------------
    @classmethod
    async def list_services(
        cls,
        session: AsyncSession,
        ctx: MCPCallContext,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List services for salon or dental clinic."""
        if ctx.merchant_id == "glow-salon":
            return await SalonBusinessService.list_services(session, ctx.merchant_id, category)
        elif ctx.merchant_id == "dental-clinic":
            return await DentalBusinessService.list_services(session, ctx.merchant_id, category)
        return []

    @classmethod
    async def check_available_slots(
        cls,
        session: AsyncSession,
        ctx: MCPCallContext,
        slot_date: Optional[date] = None,
        staff_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Check open appointment slots."""
        if ctx.merchant_id == "glow-salon":
            return await SalonBusinessService.check_available_slots(session, ctx.merchant_id, slot_date, staff_id)
        elif ctx.merchant_id == "dental-clinic":
            return await DentalBusinessService.check_available_slots(session, ctx.merchant_id, slot_date, staff_id)
        return []

    @classmethod
    async def book_appointment(
        cls,
        session: AsyncSession,
        ctx: MCPCallContext,
        service_id: str,
        slot_date: date,
        start_time_val: time,
        staff_id: Optional[str] = None,
        notes: Optional[str] = None,
        chief_complaint: Optional[str] = None
    ) -> Dict[str, Any]:
        """Book an appointment with double booking prevention."""
        if ctx.merchant_id == "glow-salon":
            res = await SalonBusinessService.book_appointment(
                session=session,
                merchant_id=ctx.merchant_id,
                customer_id=ctx.customer_id,
                service_id=service_id,
                slot_date=slot_date,
                start_time_val=start_time_val,
                staff_id=staff_id,
                notes=notes
            )
        elif ctx.merchant_id == "dental-clinic":
            res = await DentalBusinessService.book_appointment(
                session=session,
                merchant_id=ctx.merchant_id,
                customer_id=ctx.customer_id,
                service_id=service_id,
                slot_date=slot_date,
                start_time_val=start_time_val,
                dentist_id=staff_id,
                chief_complaint=chief_complaint
            )
        else:
            return {"success": False, "error": f"Appointments are not supported for {ctx.merchant_id}"}

        if res.get("success"):
            await AuditLogger.log_event(
                action="APPOINTMENT_BOOKED",
                resource_type="appointment",
                merchant_id=ctx.merchant_id,
                customer_phone=ctx.customer_phone,
                resource_id=res.get("booking_reference"),
                details=res
            )
        return res

    @classmethod
    async def get_appointment(
        cls,
        session: AsyncSession,
        ctx: MCPCallContext,
        booking_reference: str
    ) -> Dict[str, Any]:
        """Lookup an appointment owned by caller."""
        if ctx.merchant_id == "glow-salon":
            appt = await SalonBusinessService.get_appointment(session, ctx.merchant_id, ctx.customer_id, booking_reference)
        elif ctx.merchant_id == "dental-clinic":
            appt = await DentalBusinessService.get_appointment(session, ctx.merchant_id, ctx.customer_id, booking_reference)
        else:
            return {"error": "Invalid merchant"}

        if not appt:
            return {"error": f"Appointment {booking_reference} not found"}
        return appt

    @classmethod
    async def update_appointment(
        cls,
        session: AsyncSession,
        ctx: MCPCallContext,
        booking_reference: str,
        new_slot_date: date,
        new_start_time: time
    ) -> Dict[str, Any]:
        """Reschedule an existing appointment."""
        if ctx.merchant_id == "glow-salon":
            res = await SalonBusinessService.reschedule_appointment(
                session, ctx.merchant_id, ctx.customer_id, booking_reference, new_slot_date, new_start_time
            )
        else:
            return {"success": False, "error": "Rescheduling via assistant currently supported for Glow Salon. For dental changes, please speak to human receptionist."}

        if res.get("success"):
            await AuditLogger.log_event(
                action="APPOINTMENT_RESCHEDULED",
                resource_type="appointment",
                merchant_id=ctx.merchant_id,
                customer_phone=ctx.customer_phone,
                resource_id=booking_reference,
                details=res
            )
        return res

    @classmethod
    async def cancel_appointment(
        cls,
        session: AsyncSession,
        ctx: MCPCallContext,
        booking_reference: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Cancel an existing appointment and release the slot."""
        if ctx.merchant_id == "glow-salon":
            res = await SalonBusinessService.cancel_appointment(session, ctx.merchant_id, ctx.customer_id, booking_reference, reason)
        elif ctx.merchant_id == "dental-clinic":
            res = await DentalBusinessService.cancel_appointment(session, ctx.merchant_id, ctx.customer_id, booking_reference, reason)
        else:
            return {"success": False, "error": "Invalid merchant"}

        if res.get("success"):
            await AuditLogger.log_event(
                action="APPOINTMENT_CANCELLED",
                resource_type="appointment",
                merchant_id=ctx.merchant_id,
                customer_phone=ctx.customer_phone,
                resource_id=booking_reference,
                details={"reason": reason}
            )
        return res

    # -------------------------------------------------------------------------
    # CUSTOMER & SUPPORT TOOLS
    # -------------------------------------------------------------------------
    @classmethod
    async def get_customer_profile(
        cls,
        session: AsyncSession,
        ctx: MCPCallContext
    ) -> Dict[str, Any]:
        """Get customer profile for the active merchant."""
        prof = await CustomerService.get_or_create_merchant_profile(session, ctx.customer_id, ctx.merchant_id)
        return {
            "preferred_name": prof.preferred_name,
            "interaction_count": prof.interaction_count,
            "notes": prof.notes
        }

    @classmethod
    async def create_support_escalation(
        cls,
        session: AsyncSession,
        ctx: MCPCallContext,
        reason: str,
        category: str = "general",
        urgency: str = "medium"
    ) -> Dict[str, Any]:
        """Escalate conversation to human staff."""
        res = await EscalationService.create_escalation(
            session=session,
            merchant_id=ctx.merchant_id,
            customer_id=ctx.customer_id,
            reason=reason,
            category=category,
            urgency=urgency,
            conversation_id=ctx.conversation_id
        )
        await AuditLogger.log_event(
            action="SUPPORT_ESCALATED",
            resource_type="escalation",
            merchant_id=ctx.merchant_id,
            customer_phone=ctx.customer_phone,
            resource_id=res.get("escalation_id"),
            details={"reason": reason, "category": category, "urgency": urgency}
        )
        return res
