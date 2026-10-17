from typing import List, Optional, Dict, Any
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.app.core.database import get_db
from backend.app.models.shared import Merchant
from backend.app.models.grocery import GroceryProduct, GroceryInventory
from backend.app.models.sweets import SweetsProduct, SweetsInventory
from backend.app.models.salon import SalonService
from backend.app.models.dental import DentalService
from backend.app.api.deps import get_current_merchant

router = APIRouter(prefix="/catalog", tags=["Products & Services"])

class ProductCreateRequest(BaseModel):
    name: str
    category: str
    price: float
    unit: str = "piece"
    stock_quantity: int = 10
    description: Optional[str] = None
    is_sugar_free: bool = False
    duration_minutes: int = 60

class StockUpdateRequest(BaseModel):
    stock_quantity: int

@router.get("/items")
async def list_catalog_items(
    merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    """List catalog products or services for current merchant."""
    m_id = merchant.id
    b_type = merchant.business_type

    if b_type == "grocery":
        stmt = select(GroceryProduct).options(selectinload(GroceryProduct.inventory)).where(GroceryProduct.merchant_id == m_id)
        prods = (await db.execute(stmt)).scalars().all()
        return [
            {
                "id": p.id,
                "name": p.name,
                "category": p.category,
                "unit": p.unit,
                "price": float(p.price),
                "stock": p.inventory.stock_quantity if p.inventory else 0,
                "is_active": p.is_active,
                "description": p.description,
                "type": "product"
            }
            for p in prods
        ]

    elif b_type == "sweets":
        stmt = select(SweetsProduct).options(selectinload(SweetsProduct.inventory)).where(SweetsProduct.merchant_id == m_id)
        prods = (await db.execute(stmt)).scalars().all()
        return [
            {
                "id": p.id,
                "name": p.name,
                "category": p.category,
                "unit": p.unit,
                "price": float(p.price),
                "stock": p.inventory.stock_quantity if p.inventory else 0,
                "is_sugar_free": p.is_sugar_free,
                "is_active": p.is_active,
                "description": p.description,
                "type": "sweet"
            }
            for p in prods
        ]

    elif b_type == "salon":
        stmt = select(SalonService).where(SalonService.merchant_id == m_id)
        services = (await db.execute(stmt)).scalars().all()
        return [
            {
                "id": s.id,
                "name": s.name,
                "category": s.category,
                "duration_minutes": s.duration_minutes,
                "price": float(s.price),
                "is_active": s.is_active,
                "description": s.description,
                "type": "service"
            }
            for s in services
        ]

    elif b_type == "dental":
        stmt = select(DentalService).where(DentalService.merchant_id == m_id)
        services = (await db.execute(stmt)).scalars().all()
        return [
            {
                "id": s.id,
                "name": s.name,
                "category": s.category,
                "duration_minutes": s.duration_minutes,
                "price": float(s.consultation_fee),
                "is_active": s.is_active,
                "description": s.description,
                "type": "service"
            }
            for s in services
        ]
    return []

@router.post("/items")
async def create_catalog_item(
    req: ProductCreateRequest,
    merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    """Create a new product or service for this merchant."""
    m_id = merchant.id
    b_type = merchant.business_type

    if b_type == "grocery":
        prod = GroceryProduct(
            merchant_id=m_id,
            name=req.name,
            category=req.category,
            unit=req.unit,
            price=Decimal(str(req.price)),
            description=req.description
        )
        db.add(prod)
        inv = GroceryInventory(product=prod, stock_quantity=req.stock_quantity)
        db.add(inv)
        await db.commit()
        return {"id": prod.id, "name": prod.name, "status": "created"}

    elif b_type == "sweets":
        prod = SweetsProduct(
            merchant_id=m_id,
            name=req.name,
            category=req.category,
            unit=req.unit,
            price=Decimal(str(req.price)),
            description=req.description,
            is_sugar_free=req.is_sugar_free
        )
        db.add(prod)
        inv = SweetsInventory(product=prod, stock_quantity=req.stock_quantity)
        db.add(inv)
        await db.commit()
        return {"id": prod.id, "name": prod.name, "status": "created"}

    elif b_type == "salon":
        serv = SalonService(
            merchant_id=m_id,
            name=req.name,
            category=req.category,
            duration_minutes=req.duration_minutes,
            price=Decimal(str(req.price)),
            description=req.description
        )
        db.add(serv)
        await db.commit()
        return {"id": serv.id, "name": serv.name, "status": "created"}

    elif b_type == "dental":
        serv = DentalService(
            merchant_id=m_id,
            name=req.name,
            category=req.category,
            duration_minutes=req.duration_minutes,
            consultation_fee=Decimal(str(req.price)),
            description=req.description
        )
        db.add(serv)
        await db.commit()
        return {"id": serv.id, "name": serv.name, "status": "created"}

@router.put("/items/{item_id}/stock")
async def update_item_stock(
    item_id: str,
    req: StockUpdateRequest,
    merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    """Adjust live stock quantity for grocery or sweets item."""
    if merchant.business_type == "grocery":
        stmt = select(GroceryInventory).where(GroceryInventory.product_id == item_id)
        inv = (await db.execute(stmt)).scalars().first()
        if not inv:
            raise HTTPException(status_code=404, detail="Product inventory record not found")
        inv.stock_quantity = req.stock_quantity
        await db.commit()
        return {"item_id": item_id, "stock_quantity": inv.stock_quantity}

    elif merchant.business_type == "sweets":
        stmt = select(SweetsInventory).where(SweetsInventory.product_id == item_id)
        inv = (await db.execute(stmt)).scalars().first()
        if not inv:
            raise HTTPException(status_code=404, detail="Sweets inventory record not found")
        inv.stock_quantity = req.stock_quantity
        await db.commit()
        return {"item_id": item_id, "stock_quantity": inv.stock_quantity}

    raise HTTPException(status_code=400, detail="Inventory adjustments not applicable for services")


class ProductUpdateRequest(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    unit: Optional[str] = None
    stock_quantity: Optional[int] = None
    description: Optional[str] = None
    is_sugar_free: Optional[bool] = None
    duration_minutes: Optional[int] = None
    is_active: Optional[bool] = None


@router.put("/items/{item_id}")
async def update_catalog_item(
    item_id: str,
    req: ProductUpdateRequest,
    merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    """Update catalog item attributes for current merchant."""
    m_id = merchant.id
    b_type = merchant.business_type

    if b_type == "grocery":
        stmt = select(GroceryProduct).options(selectinload(GroceryProduct.inventory)).where(
            GroceryProduct.id == item_id,
            GroceryProduct.merchant_id == m_id
        )
        prod = (await db.execute(stmt)).scalars().first()
        if not prod:
            raise HTTPException(status_code=404, detail="Product not found")
        if req.name is not None:
            prod.name = req.name
        if req.category is not None:
            prod.category = req.category
        if req.unit is not None:
            prod.unit = req.unit
        if req.price is not None:
            prod.price = Decimal(str(req.price))
        if req.description is not None:
            prod.description = req.description
        if req.is_active is not None:
            prod.is_active = req.is_active
        if req.stock_quantity is not None:
            if prod.inventory:
                prod.inventory.stock_quantity = req.stock_quantity
            else:
                inv = GroceryInventory(product_id=prod.id, stock_quantity=req.stock_quantity)
                db.add(inv)
        await db.commit()
        return {"id": prod.id, "name": prod.name, "status": "updated"}

    elif b_type == "sweets":
        stmt = select(SweetsProduct).options(selectinload(SweetsProduct.inventory)).where(
            SweetsProduct.id == item_id,
            SweetsProduct.merchant_id == m_id
        )
        prod = (await db.execute(stmt)).scalars().first()
        if not prod:
            raise HTTPException(status_code=404, detail="Product not found")
        if req.name is not None:
            prod.name = req.name
        if req.category is not None:
            prod.category = req.category
        if req.unit is not None:
            prod.unit = req.unit
        if req.price is not None:
            prod.price = Decimal(str(req.price))
        if req.description is not None:
            prod.description = req.description
        if req.is_sugar_free is not None:
            prod.is_sugar_free = req.is_sugar_free
        if req.is_active is not None:
            prod.is_active = req.is_active
        if req.stock_quantity is not None:
            if prod.inventory:
                prod.inventory.stock_quantity = req.stock_quantity
            else:
                inv = SweetsInventory(product_id=prod.id, stock_quantity=req.stock_quantity)
                db.add(inv)
        await db.commit()
        return {"id": prod.id, "name": prod.name, "status": "updated"}

    elif b_type == "salon":
        stmt = select(SalonService).where(
            SalonService.id == item_id,
            SalonService.merchant_id == m_id
        )
        serv = (await db.execute(stmt)).scalars().first()
        if not serv:
            raise HTTPException(status_code=404, detail="Service not found")
        if req.name is not None:
            serv.name = req.name
        if req.category is not None:
            serv.category = req.category
        if req.duration_minutes is not None:
            serv.duration_minutes = req.duration_minutes
        if req.price is not None:
            serv.price = Decimal(str(req.price))
        if req.description is not None:
            serv.description = req.description
        if req.is_active is not None:
            serv.is_active = req.is_active
        await db.commit()
        return {"id": serv.id, "name": serv.name, "status": "updated"}

    elif b_type == "dental":
        stmt = select(DentalService).where(
            DentalService.id == item_id,
            DentalService.merchant_id == m_id
        )
        serv = (await db.execute(stmt)).scalars().first()
        if not serv:
            raise HTTPException(status_code=404, detail="Service not found")
        if req.name is not None:
            serv.name = req.name
        if req.category is not None:
            serv.category = req.category
        if req.duration_minutes is not None:
            serv.duration_minutes = req.duration_minutes
        if req.price is not None:
            serv.consultation_fee = Decimal(str(req.price))
        if req.description is not None:
            serv.description = req.description
        if req.is_active is not None:
            serv.is_active = req.is_active
        await db.commit()
        return {"id": serv.id, "name": serv.name, "status": "updated"}

    raise HTTPException(status_code=400, detail="Invalid merchant business type")


@router.delete("/items/{item_id}")
async def delete_catalog_item(
    item_id: str,
    merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    """Delete a catalog product or service for the current merchant."""
    m_id = merchant.id
    b_type = merchant.business_type

    if b_type == "grocery":
        stmt = select(GroceryProduct).options(selectinload(GroceryProduct.inventory)).where(
            GroceryProduct.id == item_id,
            GroceryProduct.merchant_id == m_id
        )
        prod = (await db.execute(stmt)).scalars().first()
        if not prod:
            raise HTTPException(status_code=404, detail="Product not found")
        await db.delete(prod)
        await db.commit()
        return {"id": item_id, "status": "deleted"}

    elif b_type == "sweets":
        stmt = select(SweetsProduct).options(selectinload(SweetsProduct.inventory)).where(
            SweetsProduct.id == item_id,
            SweetsProduct.merchant_id == m_id
        )
        prod = (await db.execute(stmt)).scalars().first()
        if not prod:
            raise HTTPException(status_code=404, detail="Product not found")
        await db.delete(prod)
        await db.commit()
        return {"id": item_id, "status": "deleted"}

    elif b_type == "salon":
        stmt = select(SalonService).where(
            SalonService.id == item_id,
            SalonService.merchant_id == m_id
        )
        serv = (await db.execute(stmt)).scalars().first()
        if not serv:
            raise HTTPException(status_code=404, detail="Service not found")
        await db.delete(serv)
        await db.commit()
        return {"id": item_id, "status": "deleted"}

    elif b_type == "dental":
        stmt = select(DentalService).where(
            DentalService.id == item_id,
            DentalService.merchant_id == m_id
        )
        serv = (await db.execute(stmt)).scalars().first()
        if not serv:
            raise HTTPException(status_code=404, detail="Service not found")
        await db.delete(serv)
        await db.commit()
        return {"id": item_id, "status": "deleted"}

    raise HTTPException(status_code=400, detail="Invalid merchant business type")

