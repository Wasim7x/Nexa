from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.models.shared import Merchant, MerchantSettings, MerchantUser, AuditLog
from backend.app.ai.router import get_ai_provider
from backend.app.api.deps import get_current_merchant, get_current_user
from backend.app.guardrails.audit_logger import AuditLogger

router = APIRouter(prefix="/settings", tags=["Settings & Integrations"])

class AISettingsUpdateRequest(BaseModel):
    ai_provider: str  # 'gemini', 'openai', 'groq', 'ollama', 'mock'
    ai_model: Optional[str] = None
    api_key: Optional[str] = None  # Updated securely on backend

class GeneralSettingsUpdateRequest(BaseModel):
    business_hours: Optional[str] = None
    timezone: Optional[str] = None
    notification_phone: Optional[str] = None
    escalation_message: Optional[str] = None
    welcome_message: Optional[str] = None

@router.get("")
async def get_settings(
    merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve settings without leaking sensitive API keys."""
    stmt = select(MerchantSettings).where(MerchantSettings.merchant_id == merchant.id)
    ms = (await db.execute(stmt)).scalars().first()

    return {
        "merchant": {
            "id": merchant.id,
            "name": merchant.name,
            "business_type": merchant.business_type,
            "phone_number": merchant.phone_number,
            "description": merchant.description
        },
        "settings": {
            "business_hours": ms.business_hours if ms else "Mon-Sun: 9:00 AM - 9:00 PM",
            "timezone": ms.timezone if ms else "UTC",
            "notification_phone": ms.notification_phone if ms else None,
            "notification_channel": ms.notification_channel if ms else "whatsapp",
            "escalation_message": ms.escalation_message if ms else "",
            "welcome_message": ms.welcome_message if ms else "",
            "ai_provider": ms.ai_provider if ms else "mock",
            "ai_model": ms.ai_model if ms else "default"
        },
        "whatsapp_integration": {
            "status": "connected" if (settings.WHATSAPP_ACCESS_TOKEN or settings.USE_MOCK_WHATSAPP) else "unconfigured",
            "mode": "simulator" if settings.USE_MOCK_WHATSAPP else "cloud_api",
            "phone_number_id": settings.WHATSAPP_PHONE_NUMBER_ID or "simulated-phone-id",
            "webhook_verified": True
        }
    }

@router.put("/general")
async def update_general_settings(
    req: GeneralSettingsUpdateRequest,
    merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    """Update merchant operational hours and notification messages."""
    stmt = select(MerchantSettings).where(MerchantSettings.merchant_id == merchant.id)
    ms = (await db.execute(stmt)).scalars().first()
    if not ms:
        ms = MerchantSettings(merchant_id=merchant.id)
        db.add(ms)

    if req.business_hours is not None:
        ms.business_hours = req.business_hours
    if req.timezone is not None:
        ms.timezone = req.timezone
    if req.notification_phone is not None:
        ms.notification_phone = req.notification_phone
    if req.escalation_message is not None:
        ms.escalation_message = req.escalation_message
    if req.welcome_message is not None:
        ms.welcome_message = req.welcome_message

    await db.commit()
    return {"status": "updated", "merchant_id": merchant.id}

@router.post("/ai/test-connection")
async def test_ai_connection(
    req: AISettingsUpdateRequest,
    merchant: Merchant = Depends(get_current_merchant)
):
    """Test AI provider connectivity without persisting credentials if invalid."""
    provider = get_ai_provider(provider_name=req.ai_provider, model_name=req.ai_model)
    if req.api_key:
        provider.api_key = req.api_key

    result = await provider.test_connection()
    return result

@router.put("/ai")
async def update_ai_settings(
    req: AISettingsUpdateRequest,
    merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    """Update merchant active AI provider."""
    stmt = select(MerchantSettings).where(MerchantSettings.merchant_id == merchant.id)
    ms = (await db.execute(stmt)).scalars().first()
    if not ms:
        ms = MerchantSettings(merchant_id=merchant.id)
        db.add(ms)

    ms.ai_provider = req.ai_provider
    if req.ai_model:
        ms.ai_model = req.ai_model

    await db.commit()
    return {"status": "ai_settings_updated", "ai_provider": ms.ai_provider, "ai_model": ms.ai_model}

@router.get("/audit-logs")
async def get_audit_logs(
    limit: int = 50,
    merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve security and business audit logs for active merchant."""
    stmt = (
        select(AuditLog)
        .where(AuditLog.merchant_id == merchant.id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    res = await db.execute(stmt)
    logs = res.scalars().all()

    return [
        {
            "id": l.id,
            "action": l.action,
            "resource_type": l.resource_type,
            "resource_id": l.resource_id,
            "status": l.status,
            "customer_phone": l.customer_phone,
            "details": l.details_json,
            "created_at": l.created_at.isoformat()
        }
        for l in logs
    ]
