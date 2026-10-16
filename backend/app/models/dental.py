from typing import Optional, List
from decimal import Decimal
from datetime import datetime, date, time, timezone
from sqlalchemy import String, Text, Numeric, Integer, Boolean, ForeignKey, Date, Time, DateTime, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin, generate_uuid

class DentalService(Base, TimestampMixin):
    __tablename__ = "dental_services"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    merchant_id: Mapped[str] = mapped_column(String(64), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)  # 'Consultation', 'Preventative', 'Cosmetic', 'Orthodontics', 'Restorative'
    duration_minutes: Mapped[int] = mapped_column(Integer, default=45, nullable=False)
    consultation_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    appointments: Mapped[List["DentalAppointment"]] = relationship("DentalAppointment", back_populates="service")

class DentalStaff(Base, TimestampMixin):
    __tablename__ = "dental_staff"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    merchant_id: Mapped[str] = mapped_column(String(64), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(String(64), default="Dentist")  # 'Dr.', 'Orthodontist', 'Dental Hygienist'
    license_number: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    specialties: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    availabilities: Mapped[List["DentalAvailability"]] = relationship("DentalAvailability", back_populates="dentist", cascade="all, delete-orphan")
    appointments: Mapped[List["DentalAppointment"]] = relationship("DentalAppointment", back_populates="dentist")

class DentalAvailability(Base):
    __tablename__ = "dental_availability"
    __table_args__ = (
        UniqueConstraint("dentist_id", "slot_date", "start_time", name="uq_dental_staff_slot"),
        Index("ix_dental_slot_search", "merchant_id", "slot_date", "is_booked"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    merchant_id: Mapped[str] = mapped_column(String(64), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    dentist_id: Mapped[str] = mapped_column(String(64), ForeignKey("dental_staff.id", ondelete="CASCADE"), nullable=False)
    slot_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    is_booked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    dentist: Mapped["DentalStaff"] = relationship("DentalStaff", back_populates="availabilities")

class DentalAppointment(Base, TimestampMixin):
    __tablename__ = "dental_appointments"
    __table_args__ = (
        Index("ix_dental_appointments_merchant_cust", "merchant_id", "customer_id"),
        Index("ix_dental_appointments_date_status", "merchant_id", "appointment_date", "status"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    booking_reference: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    merchant_id: Mapped[str] = mapped_column(String(64), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(String(64), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    service_id: Mapped[str] = mapped_column(String(64), ForeignKey("dental_services.id"), nullable=False)
    dentist_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("dental_staff.id"), nullable=True)
    appointment_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="confirmed", nullable=False)  # 'confirmed', 'completed', 'rescheduled', 'cancelled'
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    chief_complaint: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Administrative only, not clinical diagnosis
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    service: Mapped["DentalService"] = relationship("DentalService", back_populates="appointments")
    dentist: Mapped[Optional["DentalStaff"]] = relationship("DentalStaff", back_populates="appointments")
