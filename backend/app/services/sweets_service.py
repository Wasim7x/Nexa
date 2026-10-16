import random
import string
from typing import List, Dict, Any, Optional
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from backend.app.models.sweets import SweetsProduct, SweetsInventory, SweetsOrder, SweetsOrderItem
from backend.app.models.shared import KnowledgeDocument
from backend.app.guardrails.authorization import AuthorizationGuardrail

class SweetsService:
    """Business service for Royal Sweets & Delights operations."""

    @classmethod
    async def search_products(
        cls,
        session: AsyncSession,
        merchant_id: str,
        query: Optional[str] = None,
        category: Optional[str] = None,
        sugar_free_only: bool = False
    ) -> List[Dict[str, Any]]:
        """Search sweets catalog with inventory and dietary filters."""
        stmt = (
            select(SweetsProduct)
            .options(selectinload(SweetsProduct.inventory))
            .where(SweetsProduct.merchant_id == merchant_id, SweetsProduct.is_active == True)
        )
        if sugar_free_only:
            stmt = stmt.where(SweetsProduct.is_sugar_free == True)
        if category:
            stmt = stmt.where(SweetsProduct.category.ilike(f"%{category}%"))
        if query:
            stmt = stmt.where(SweetsProduct.name.ilike(f"%{query}%"))

        result = await session.execute(stmt)
        products = result.scalars().all()

        return [
            {
                "product_id": p.id,
                "name": p.name,
                "category": p.category,
                "unit": p.unit,
                "price": float(p.price),
                "is_sugar_free": p.is_sugar_free,
                "in_stock": p.inventory.stock_quantity if p.inventory else 0,
                "freshness": p.inventory.batch_freshness_date if p.inventory else "Daily fresh",
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
        """Get authoritative price and stock for sweets."""
        stmt = (
            select(SweetsProduct)
            .options(selectinload(SweetsProduct.inventory))
            .where(SweetsProduct.merchant_id == merchant_id, SweetsProduct.id == product_id)
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
            "is_sugar_free": p.is_sugar_free,
            "stock_quantity": p.inventory.stock_quantity if p.inventory else 0,
            "description": p.description
        }

    @classmethod
    async def get_active_offers(
        cls,
        session: AsyncSession,
        merchant_id: str
    ) -> List[Dict[str, Any]]:
        """Get active sweets promotions and gift hampers."""
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
        items: List[Dict[str, Any]],
        order_type: str = "pickup",
        delivery_address: Optional[str] = None,
        gift_packaging: bool = False,
        gift_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a sweets order with optional gift packaging and delivery details."""
        if not items:
            return {"success": False, "error": "Order must contain at least one item."}

        order_items = []
        total_amount = Decimal("0.00")

        for item_data in items:
            prod_id = item_data.get("product_id")
            qty = int(item_data.get("quantity", 1))
            if qty <= 0:
                return {"success": False, "error": "Quantity must be greater than zero."}

            stmt = (
                select(SweetsProduct)
                .options(selectinload(SweetsProduct.inventory))
                .where(SweetsProduct.merchant_id == merchant_id, SweetsProduct.id == prod_id)
            )
            result = await session.execute(stmt)
            product = result.scalars().first()
            if not product:
                return {"success": False, "error": f"Sweet product {prod_id} not found."}

            if not product.inventory or product.inventory.stock_quantity < qty:
                return {
                    "success": False,
                    "error": f"Insufficient stock for {product.name}. Available: {product.inventory.stock_quantity if product.inventory else 0}"
                }

            product.inventory.stock_quantity -= qty
            line_total = product.price * Decimal(qty)
            total_amount += line_total

            order_items.append(SweetsOrderItem(
                product_id=product.id,
                product_name=product.name,
                quantity=qty,
                unit_price=product.price,
                total_price=line_total
            ))

        # Gift packaging nominal fee if applicable
        if gift_packaging:
            total_amount += Decimal("3.00")

        order_num = f"SWT-{''.join(random.choices(string.digits, k=6))}"

        order = SweetsOrder(
            order_number=order_num,
            merchant_id=merchant_id,
            customer_id=customer_id,
            status="confirmed",
            total_amount=total_amount,
            order_type=order_type,
            delivery_address=delivery_address if order_type == "delivery" else None,
            gift_packaging=gift_packaging,
            gift_message=gift_message,
            items=order_items
        )
        session.add(order)
        await session.flush()

        return {
            "success": True,
            "order_number": order.order_number,
            "total_amount": float(total_amount),
            "order_type": order.order_type,
            "status": order.status,
            "gift_packaging": gift_packaging,
            "item_count": len(order_items)
        }

    @classmethod
    async def get_order(
        cls,
        session: AsyncSession,
        merchant_id: str,
        customer_id: str,
        order_number: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve sweets order with ownership verification."""
        stmt = (
            select(SweetsOrder)
            .options(selectinload(SweetsOrder.items))
            .where(
                SweetsOrder.merchant_id == merchant_id,
                SweetsOrder.order_number == order_number
            )
        )
        result = await session.execute(stmt)
        order = result.scalars().first()
        if not order:
            return None

        if not AuthorizationGuardrail.verify_customer_ownership(order.customer_id, customer_id):
            raise PermissionError("Access denied: You do not own this order record.")

        return {
            "order_number": order.order_number,
            "status": order.status,
            "total_amount": float(order.total_amount),
            "order_type": order.order_type,
            "gift_packaging": order.gift_packaging,
            "gift_message": order.gift_message,
            "created_at": order.created_at.isoformat(),
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
        """Cancel sweets order and restock sweets inventory."""
        stmt = (
            select(SweetsOrder)
            .options(selectinload(SweetsOrder.items))
            .where(
                SweetsOrder.merchant_id == merchant_id,
                SweetsOrder.order_number == order_number
            )
        )
        result = await session.execute(stmt)
        order = result.scalars().first()
        if not order:
            return {"success": False, "error": f"Order {order_number} not found."}

        if not AuthorizationGuardrail.verify_customer_ownership(order.customer_id, customer_id):
            raise PermissionError("Access denied: You cannot cancel another customer's order.")

        if order.status in ["delivered", "cancelled", "ready_for_pickup"]:
            return {"success": False, "error": f"Order is {order.status} and cannot be cancelled automatically."}

        for it in order.items:
            inv_stmt = select(SweetsInventory).where(SweetsInventory.product_id == it.product_id)
            inv_res = await session.execute(inv_stmt)
            inv = inv_res.scalars().first()
            if inv:
                inv.stock_quantity += it.quantity

        order.status = "cancelled"
        await session.flush()

        return {
            "success": True,
            "order_number": order.order_number,
            "status": "cancelled",
            "message": "Sweets order successfully cancelled."
        }
