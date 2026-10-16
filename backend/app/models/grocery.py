from typing import Optional, List
from decimal import Decimal
from sqlalchemy import String, Text, Numeric, Integer, Boolean, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin, generate_uuid

class GroceryProduct(Base, TimestampMixin):
    __tablename__ = "grocery_products"
    __table_args__ = (
        Index("ix_grocery_merchant_category", "merchant_id", "category"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    merchant_id: Mapped[str] = mapped_column(String(64), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    sku: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False)  # 'Dairy', 'Produce', 'Beverages', 'Bakery', 'Pantry'
    unit: Mapped[str] = mapped_column(String(32), default="piece")  # 'kg', 'liter', 'pack', 'piece'
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    inventory: Mapped[Optional["GroceryInventory"]] = relationship("GroceryInventory", back_populates="product", uselist=False, cascade="all, delete-orphan")

class GroceryInventory(Base, TimestampMixin):
    __tablename__ = "grocery_inventory"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    product_id: Mapped[str] = mapped_column(String(64), ForeignKey("grocery_products.id", ondelete="CASCADE"), unique=True, nullable=False)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    low_stock_threshold: Mapped[int] = mapped_column(Integer, default=10, nullable=False)

    product: Mapped["GroceryProduct"] = relationship("GroceryProduct", back_populates="inventory")

class GroceryOrder(Base, TimestampMixin):
    __tablename__ = "grocery_orders"
    __table_args__ = (
        Index("ix_grocery_orders_merchant_cust", "merchant_id", "customer_id"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    order_number: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    merchant_id: Mapped[str] = mapped_column(String(64), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(String(64), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="confirmed", nullable=False)  # 'pending', 'confirmed', 'packed', 'out_for_delivery', 'delivered', 'cancelled'
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    delivery_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    items: Mapped[List["GroceryOrderItem"]] = relationship("GroceryOrderItem", back_populates="order", cascade="all, delete-orphan")

class GroceryOrderItem(Base):
    __tablename__ = "grocery_order_items"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    order_id: Mapped[str] = mapped_column(String(64), ForeignKey("grocery_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[str] = mapped_column(String(64), ForeignKey("grocery_products.id"), nullable=False)
    product_name: Mapped[str] = mapped_column(String(128), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    order: Mapped["GroceryOrder"] = relationship("GroceryOrder", back_populates="items")
