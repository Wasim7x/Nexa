import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import String, Text, Boolean, Integer, ForeignKey, DateTime, JSON, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin, generate_uuid

class Merchant(Base, TimestampMixin):
    __tablename__ = "merchants"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    business_type: Mapped[str] = mapped_column(String(64), nullable=False)  # 'grocery', 'sweets', 'salon', 'dental'
    phone_number: Mapped[str] = mapped_column(String(32), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    users: Mapped[List["MerchantUser"]] = relationship("MerchantUser", back_populates="merchant", cascade="all, delete-orphan")
    settings: Mapped[Optional["MerchantSettings"]] = relationship("MerchantSettings", back_populates="merchant", uselist=False, cascade="all, delete-orphan")
    knowledge_docs: Mapped[List["KnowledgeDocument"]] = relationship("KnowledgeDocument", back_populates="merchant", cascade="all, delete-orphan")
    customer_profiles: Mapped[List["CustomerMerchantProfile"]] = relationship("CustomerMerchantProfile", back_populates="merchant")
    escalations: Mapped[List["SupportEscalation"]] = relationship("SupportEscalation", back_populates="merchant")

class MerchantUser(Base, TimestampMixin):
    __tablename__ = "merchant_users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    merchant_id: Mapped[str] = mapped_column(String(64), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(128), nullable=False)
    role: Mapped[str] = mapped_column(String(32), default="admin", nullable=False)  # 'admin', 'staff', 'support'
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    merchant: Mapped["Merchant"] = relationship("Merchant", back_populates="users")

class Customer(Base, TimestampMixin):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    whatsapp_phone: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    # Relationships
    merchant_profiles: Mapped[List["CustomerMerchantProfile"]] = relationship("CustomerMerchantProfile", back_populates="customer", cascade="all, delete-orphan")
    conversations: Mapped[List["Conversation"]] = relationship("Conversation", back_populates="customer")

class CustomerMerchantProfile(Base, TimestampMixin):
    __tablename__ = "customer_merchant_profiles"
    __table_args__ = (
        UniqueConstraint("customer_id", "merchant_id", name="uq_customer_merchant"),
        Index("ix_customer_merchant_lookup", "customer_id", "merchant_id"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    customer_id: Mapped[str] = mapped_column(String(64), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    merchant_id: Mapped[str] = mapped_column(String(64), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False)
    preferred_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    opt_in_promotions: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    interaction_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_interaction_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    customer: Mapped["Customer"] = relationship("Customer", back_populates="merchant_profiles")
    merchant: Mapped["Merchant"] = relationship("Merchant", back_populates="customer_profiles")

class Conversation(Base, TimestampMixin):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    customer_id: Mapped[str] = mapped_column(String(64), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    active_merchant_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("merchants.id", ondelete="SET NULL"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)  # 'active', 'awaiting_human', 'resolved'
    channel: Mapped[str] = mapped_column(String(32), default="whatsapp", nullable=False)
    last_message_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    customer: Mapped["Customer"] = relationship("Customer", back_populates="conversations")
    messages: Mapped[List["Message"]] = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    conversation_id: Mapped[str] = mapped_column(String(64), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    merchant_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("merchants.id", ondelete="SET NULL"), nullable=True, index=True)
    sender_type: Mapped[str] = mapped_column(String(32), nullable=False)  # 'customer', 'ai_assistant', 'human_agent', 'system'
    direction: Mapped[str] = mapped_column(String(16), nullable=False)  # 'inbound', 'outbound'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")

class KnowledgeDocument(Base, TimestampMixin):
    __tablename__ = "knowledge_documents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    merchant_id: Mapped[str] = mapped_column(String(64), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    doc_type: Mapped[str] = mapped_column(String(32), nullable=False)  # 'faq', 'policy', 'offer', 'pdf', 'csv', 'txt'
    file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    embedding_status: Mapped[str] = mapped_column(String(32), default="indexed", nullable=False)  # 'pending', 'indexed', 'failed'
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    merchant: Mapped["Merchant"] = relationship("Merchant", back_populates="knowledge_docs")

class MerchantSettings(Base, TimestampMixin):
    __tablename__ = "merchant_settings"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    merchant_id: Mapped[str] = mapped_column(String(64), ForeignKey("merchants.id", ondelete="CASCADE"), unique=True, nullable=False)
    business_hours: Mapped[Optional[str]] = mapped_column(String(255), default="Mon-Sun: 9:00 AM - 9:00 PM")
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    notification_phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    notification_channel: Mapped[str] = mapped_column(String(32), default="whatsapp")  # 'whatsapp', 'email', 'sms'
    escalation_message: Mapped[str] = mapped_column(
        Text,
        default="I am forwarding your query to our human support assistant. They will contact you shortly."
    )
    welcome_message: Mapped[str] = mapped_column(
        Text,
        default="Hello! Welcome to our store. How can I assist you today?"
    )
    ai_provider: Mapped[str] = mapped_column(String(32), default="mock")
    ai_model: Mapped[str] = mapped_column(String(64), default="default")
    response_settings: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    merchant: Mapped["Merchant"] = relationship("Merchant", back_populates="settings")

class SupportEscalation(Base, TimestampMixin):
    __tablename__ = "support_escalations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    merchant_id: Mapped[str] = mapped_column(String(64), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(String(64), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(64), default="general")  # 'dental_clinical', 'dispute', 'refund', 'complaint', 'technical'
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)  # 'pending', 'in_progress', 'resolved', 'closed'
    urgency: Mapped[str] = mapped_column(String(16), default="medium", nullable=False)  # 'low', 'medium', 'high', 'emergency'
    assigned_to: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    merchant: Mapped["Merchant"] = relationship("Merchant", back_populates="escalations")

class NotificationJob(Base, TimestampMixin):
    __tablename__ = "notification_jobs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    merchant_id: Mapped[str] = mapped_column(String(64), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(String(64), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)  # 'order.created', 'appointment.reminder_due', etc.
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)  # 'pending', 'queued', 'sent', 'failed', 'cancelled'
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    payload_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(128), unique=True, index=True, nullable=True)

class NotificationEvent(Base):
    __tablename__ = "notification_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    job_id: Mapped[str] = mapped_column(String(64), ForeignKey("notification_jobs.id", ondelete="CASCADE"), nullable=False)
    merchant_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_response: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    merchant_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    customer_phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="success", nullable=False)  # 'success', 'denied', 'failed'
    details_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
