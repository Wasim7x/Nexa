import random
import string
from typing import List, Dict, Any, Optional
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from backend.app.models.grocery import GroceryProduct, GroceryInventory, GroceryOrder, GroceryOrderItem
from backend.app.models.shared import KnowledgeDocument
from backend.app.guardrails.authorization import AuthorizationGuardrail

class GroceryService:
    """Business service for FreshMart Grocery operations."""

    @classmethod
    async def search_products(
        cls,
        session: AsyncSession,
        merchant_id: str,
        query: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search products with inventory stock levels."""
        stmt = (
            select(GroceryProduct)
            .options(selectinload(GroceryProduct.inventory))
            .where(GroceryProduct.merchant_id == merchant_id, GroceryProduct.is_active == True)
        )
        if category:
            stmt = stmt.where(GroceryProduct.category.ilike(f"%{category}%"))
        if query:
            stmt = stmt.where(GroceryProduct.name.ilike(f"%{query}%"))

        result = await session.execute(stmt)
        products = result.scalars().all()

        return [
            {
                "product_id": p.id,
                "name": p.name,
                "category": p.category,
                "unit": p.unit,
                "price": float(p.price),
                "in_stock": p.inventory.stock_quantity if p.inventory else 0,
                "is_available": (p.inventory.stock_quantity > 0) if p.inventory else False,
                "description": p.description
            }
            for p in products
        ]

    @classmethod
    async def get_product_details(
        cls,
        session: AsyncSession,
        merchant_id: str,
        product_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get authoritative price and inventory for a specific grocery product."""
        stmt = (
            select(GroceryProduct)
            .options(selectinload(GroceryProduct.inventory))
            .where(GroceryProduct.merchant_id == merchant_id, GroceryProduct.id == product_id)
        )
        result = await session.execute(stmt)
        p = result.scalars().first()
        if not p:
            return None

        return {
            "product_id": p.id,
            "name": p.name,
            "category": p.category,
            "unit": p.unit,
            "price": float(p.price),
            "stock_quantity": p.inventory.stock_quantity if p.inventory else 0,
            "description": p.description
        }

    @classmethod
    async def get_active_offers(
        cls,
        session: AsyncSession,
        merchant_id: str
    ) -> List[Dict[str, Any]]:
        """Get active grocery promotional offers."""
        stmt = select(KnowledgeDocument).where(
            KnowledgeDocument.merchant_id == merchant_id,
            KnowledgeDocument.doc_type == "offer",
            KnowledgeDocument.is_published == True
        )
        result = await session.execute(stmt)
        docs = result.scalars().all()
        return [{"title": d.title, "details": d.content} for d in docs]

    @classmethod
    async def create_order(
        cls,
        session: AsyncSession,
        merchant_id: str,
        customer_id: str,
        items: List[Dict[str, Any]],  # [{"product_id": ..., "quantity": ...}]
        delivery_address: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a transactional grocery order.
        Validates inventory stock, updates quantities, and calculates verified totals.
        """
        if not items:
            return {"success": False, "error": "Order must contain at least one item."}

        order_items = []
        total_amount = Decimal("0.00")

        for item_data in items:
            prod_id = item_data.get("product_id")
            qty = int(item_data.get("quantity", 1))
            if qty <= 0:
                return {"success": False, "error": "Item quantity must be greater than zero."}

            stmt = (
                select(GroceryProduct)
                .options(selectinload(GroceryProduct.inventory))
                .where(GroceryProduct.merchant_id == merchant_id, GroceryProduct.id == prod_id)
            )
            result = await session.execute(stmt)
            product = result.scalars().first()
            if not product:
                return {"success": False, "error": f"Product with ID {prod_id} not found."}

            if not product.inventory or product.inventory.stock_quantity < qty:
                return {
                    "success": False,
                    "error": f"Insufficient stock for {product.name}. Available: {product.inventory.stock_quantity if product.inventory else 0}"
                }

            # Deduct stock
            product.inventory.stock_quantity -= qty

            line_total = product.price * Decimal(qty)
            total_amount += line_total

            order_item = GroceryOrderItem(
                product_id=product.id,
                product_name=product.name,
                quantity=qty,
                unit_price=product.price,
                total_price=line_total
            )
            order_items.append(order_item)

        # Generate unique order number
        order_num = f"GRO-{''.join(random.choices(string.digits, k=6))}"

        order = GroceryOrder(
            order_number=order_num,
            merchant_id=merchant_id,
            customer_id=customer_id,
            status="confirmed",
            total_amount=total_amount,
            delivery_address=delivery_address,
            notes=notes,
            items=order_items
        )
        session.add(order)
        await session.flush()

        return {
            "success": True,
            "order_number": order.order_number,
            "total_amount": float(total_amount),
            "status": order.status,
            "item_count": len(order_items),
            "delivery_address": delivery_address
        }

    @classmethod
    async def get_order(
        cls,
        session: AsyncSession,
        merchant_id: str,
        customer_id: str,
        order_number: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve grocery order with tenant isolation and ownership verification."""
        stmt = (
            select(GroceryOrder)
            .options(selectinload(GroceryOrder.items))
            .where(
                GroceryOrder.merchant_id == merchant_id,
                GroceryOrder.order_number == order_number
            )
        )
        result = await session.execute(stmt)
        order = result.scalars().first()
        if not order:
            return None

        # IDOR Ownership check
        if not AuthorizationGuardrail.verify_customer_ownership(order.customer_id, customer_id):
            raise PermissionError("Access denied: You do not own this order record.")

        return {
            "order_number": order.order_number,
            "status": order.status,
            "total_amount": float(order.total_amount),
            "created_at": order.created_at.isoformat(),
            "delivery_address": order.delivery_address,
            "notes": order.notes,
            "items": [
                {
                    "product_name": it.product_name,
                    "quantity": it.quantity,
                    "unit_price": float(it.unit_price),
                    "total_price": float(it.total_price)
                }
                for it in order.items
            ]
        }

    @classmethod
    async def cancel_order(
        cls,
        session: AsyncSession,
        merchant_id: str,
        customer_id: str,
        order_number: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Cancel an eligible grocery order and restock inventory."""
        stmt = (
            select(GroceryOrder)
            .options(selectinload(GroceryOrder.items))
            .where(
                GroceryOrder.merchant_id == merchant_id,
                GroceryOrder.order_number == order_number
            )
        )
        result = await session.execute(stmt)
        order = result.scalars().first()
        if not order:
            return {"success": False, "error": f"Order {order_number} not found."}

        # IDOR check
        if not AuthorizationGuardrail.verify_customer_ownership(order.customer_id, customer_id):
            raise PermissionError("Access denied: You cannot cancel another customer's order.")

        if order.status in ["delivered", "cancelled"]:
            return {"success": False, "error": f"Order is already {order.status} and cannot be cancelled."}

        if order.status == "out_for_delivery":
            return {"success": False, "error": "Order is out for delivery. Please contact store support to intercept."}

        # Restock inventory
        for it in order.items:
            inv_stmt = select(GroceryInventory).where(GroceryInventory.product_id == it.product_id)
            inv_res = await session.execute(inv_stmt)
            inv = inv_res.scalars().first()
            if inv:
                inv.stock_quantity += it.quantity

        order.status = "cancelled"
        if reason:
            order.notes = f"{order.notes or ''} [Cancelled: {reason}]"
        await session.flush()

        return {
            "success": True,
            "order_number": order.order_number,
            "status": "cancelled",
            "message": "Your grocery order has been successfully cancelled and inventory restocked."
        }
