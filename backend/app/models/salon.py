from typing import Optional, List
from decimal import Decimal
from datetime import datetime, date, time, timezone
from sqlalchemy import String, Text, Numeric, Integer, Boolean, ForeignKey, Date, Time, DateTime, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin, generate_uuid

class SalonService(Base, TimestampMixin):
    __tablename__ = "salon_services"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    merchant_id: Mapped[str] = mapped_column(String(64), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)  # 'Hair Care', 'Skin & Facial', 'Nails', 'Spa & Massage', 'Bridal'
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    appointments: Mapped[List["SalonAppointment"]] = relationship("SalonAppointment", back_populates="service")

class SalonStaff(Base, TimestampMixin):
    __tablename__ = "salon_staff"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    merchant_id: Mapped[str] = mapped_column(String(64), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    role: Mapped[str] = mapped_column(String(64), default="Stylist")  # 'Senior Stylist', 'Esthetician', 'Nail Artist'
    specialties: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    availabilities: Mapped[List["SalonAvailability"]] = relationship("SalonAvailability", back_populates="staff", cascade="all, delete-orphan")
    appointments: Mapped[List["SalonAppointment"]] = relationship("SalonAppointment", back_populates="staff")

class SalonAvailability(Base):
    __tablename__ = "salon_availability"
    __table_args__ = (
        UniqueConstraint("staff_id", "slot_date", "start_time", name="uq_salon_staff_slot"),
        Index("ix_salon_slot_search", "merchant_id", "slot_date", "is_booked"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    merchant_id: Mapped[str] = mapped_column(String(64), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    staff_id: Mapped[str] = mapped_column(String(64), ForeignKey("salon_staff.id", ondelete="CASCADE"), nullable=False)
    slot_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    is_booked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    staff: Mapped["SalonStaff"] = relationship("SalonStaff", back_populates="availabilities")

class SalonAppointment(Base, TimestampMixin):
    __tablename__ = "salon_appointments"
    __table_args__ = (
        Index("ix_salon_appointments_merchant_cust", "merchant_id", "customer_id"),
        Index("ix_salon_appointments_date_status", "merchant_id", "appointment_date", "status"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    booking_reference: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    merchant_id: Mapped[str] = mapped_column(String(64), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(String(64), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    service_id: Mapped[str] = mapped_column(String(64), ForeignKey("salon_services.id"), nullable=False)
    staff_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("salon_staff.id"), nullable=True)
    appointment_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="confirmed", nullable=False)  # 'confirmed', 'completed', 'rescheduled', 'cancelled'
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    service: Mapped["SalonService"] = relationship("SalonService", back_populates="appointments")
    staff: Mapped[Optional["SalonStaff"]] = relationship("SalonStaff", back_populates="appointments")
