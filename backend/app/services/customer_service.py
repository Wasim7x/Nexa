from typing import Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from backend.app.models.shared import Customer, CustomerMerchantProfile, Conversation
from backend.app.guardrails.input_validator import InputValidator

class CustomerService:
    """Manages customer identity and merchant-specific profiles."""

    @classmethod
    async def get_or_create_customer(
        cls,
        session: AsyncSession,
        whatsapp_phone: str,
        name: Optional[str] = None,
        email: Optional[str] = None
    ) -> Customer:
        """
        Safely retrieve or create a customer record using normalized phone number.
        Handles concurrent creation gracefully.
        """
        normalized_phone = InputValidator.normalize_phone_number(whatsapp_phone)

        # 1. Try finding existing customer
        stmt = select(Customer).where(Customer.whatsapp_phone == normalized_phone)
        result = await session.execute(stmt)
        customer = result.scalars().first()

        if customer:
            if name and not customer.name:
                customer.name = name
            if email and not customer.email:
                customer.email = email
            await session.flush()
            return customer

        # 2. Insert new customer with conflict handling
        new_customer = Customer(
            whatsapp_phone=normalized_phone,
            name=name,
            email=email
        )
        session.add(new_customer)
        try:
            await session.flush()
            return new_customer
        except IntegrityError:
            # Another concurrent request already inserted the record
            await session.rollback()
            result = await session.execute(select(Customer).where(Customer.whatsapp_phone == normalized_phone))
            return result.scalars().one()

    @classmethod
    async def get_or_create_merchant_profile(
        cls,
        session: AsyncSession,
        customer_id: str,
        merchant_id: str,
        preferred_name: Optional[str] = None
    ) -> CustomerMerchantProfile:
        """Retrieve or create tenant-scoped customer profile."""
        stmt = select(CustomerMerchantProfile).where(
            CustomerMerchantProfile.customer_id == customer_id,
            CustomerMerchantProfile.merchant_id == merchant_id
        )
        result = await session.execute(stmt)
        profile = result.scalars().first()

        if profile:
            profile.interaction_count += 1
            profile.last_interaction_at = datetime.now(timezone.utc)
            if preferred_name and not profile.preferred_name:
                profile.preferred_name = preferred_name
            await session.flush()
            return profile

        new_profile = CustomerMerchantProfile(
            customer_id=customer_id,
            merchant_id=merchant_id,
            preferred_name=preferred_name,
            interaction_count=1,
            last_interaction_at=datetime.now(timezone.utc)
        )
        session.add(new_profile)
        try:
            await session.flush()
            return new_profile
        except IntegrityError:
            await session.rollback()
            result = await session.execute(stmt)
            return result.scalars().one()

    @classmethod
    async def get_or_create_conversation(
        cls,
        session: AsyncSession,
        customer_id: str,
        active_merchant_id: Optional[str] = None
    ) -> Conversation:
        """Find active conversation or create new one."""
        stmt = (
            select(Conversation)
            .where(Conversation.customer_id == customer_id, Conversation.status == "active")
            .order_by(Conversation.updated_at.desc())
        )
        result = await session.execute(stmt)
        conversation = result.scalars().first()

        if conversation:
            if active_merchant_id:
                conversation.active_merchant_id = active_merchant_id
            conversation.last_message_at = datetime.now(timezone.utc)
            await session.flush()
            return conversation

        new_convo = Conversation(
            customer_id=customer_id,
            active_merchant_id=active_merchant_id,
            status="active",
            channel="whatsapp",
            last_message_at=datetime.now(timezone.utc)
        )
        session.add(new_convo)
        await session.flush()
        return new_convo
