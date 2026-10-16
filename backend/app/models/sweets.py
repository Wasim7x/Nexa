from typing import Optional, List
from decimal import Decimal
from sqlalchemy import String, Text, Numeric, Integer, Boolean, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin, generate_uuid

class SweetsProduct(Base, TimestampMixin):
    __tablename__ = "sweets_products"
    __table_args__ = (
        Index("ix_sweets_merchant_category", "merchant_id", "category"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    merchant_id: Mapped[str] = mapped_column(String(64), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False)  # 'Dry Fruit Sweets', 'Milk Sweets', 'Bengali Sweets', 'Snacks', 'Gift Boxes'
    unit: Mapped[str] = mapped_column(String(32), default="kg")  # 'kg', 'box', 'piece', '500g'
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_sugar_free: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    inventory: Mapped[Optional["SweetsInventory"]] = relationship("SweetsInventory", back_populates="product", uselist=False, cascade="all, delete-orphan")

class SweetsInventory(Base, TimestampMixin):
    __tablename__ = "sweets_inventory"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    product_id: Mapped[str] = mapped_column(String(64), ForeignKey("sweets_products.id", ondelete="CASCADE"), unique=True, nullable=False)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    batch_freshness_date: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    product: Mapped["SweetsProduct"] = relationship("SweetsProduct", back_populates="inventory")

class SweetsOrder(Base, TimestampMixin):
    __tablename__ = "sweets_orders"
    __table_args__ = (
        Index("ix_sweets_orders_merchant_cust", "merchant_id", "customer_id"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    order_number: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    merchant_id: Mapped[str] = mapped_column(String(64), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(String(64), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="confirmed", nullable=False)  # 'pending', 'confirmed', 'packed', 'ready_for_pickup', 'delivered', 'cancelled'
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    order_type: Mapped[str] = mapped_column(String(32), default="pickup")  # 'pickup', 'delivery'
    delivery_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    gift_packaging: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    gift_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    items: Mapped[List["SweetsOrderItem"]] = relationship("SweetsOrderItem", back_populates="order", cascade="all, delete-orphan")

class SweetsOrderItem(Base):
    __tablename__ = "sweets_order_items"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    order_id: Mapped[str] = mapped_column(String(64), ForeignKey("sweets_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[str] = mapped_column(String(64), ForeignKey("sweets_products.id"), nullable=False)
    product_name: Mapped[str] = mapped_column(String(128), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    order: Mapped["SweetsOrder"] = relationship("SweetsOrder", back_populates="items")
