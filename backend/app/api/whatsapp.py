import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, Query, Header, HTTPException, status, Response
from pydantic import BaseModel

from backend.app.core.config import settings
from backend.app.whatsapp.security import WhatsAppSecurity
from backend.app.whatsapp.parser import WhatsAppPayloadParser
from backend.app.whatsapp.client import WhatsAppCloudClient, SIMULATOR_OUTBOUND_MESSAGES
from backend.app.workflows.graph import process_whatsapp_message

logger = logging.getLogger("vera.whatsapp.api")
router = APIRouter(prefix="/whatsapp", tags=["WhatsApp Webhook & Simulator"])

class SimulateMessageRequest(BaseModel):
    sender_phone: str = "+15551234567"
    message_text: str
    referral_merchant_slug: Optional[str] = None

@router.get("/webhook")
async def verify_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
):
    """
    Meta WhatsApp Cloud API Webhook Verification Endpoint.
    Validates token and returns hub.challenge as plain text.
    """
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info("WhatsApp webhook verified successfully by Meta.")
        return Response(content=hub_challenge or "", media_type="text/plain", status_code=200)

    logger.warning("WhatsApp webhook verification failed: Token mismatch.")
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verification token mismatch")

@router.post("/webhook")
async def receive_webhook(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256")
):
    """
    Meta WhatsApp Cloud API Incoming Message & Status Webhook Receiver.
    Verifies HMAC signature, deduplicates messages, and routes through LangGraph workflow.
    """
    raw_body = await request.body()

    # 1. Signature Verification
    if not WhatsAppSecurity.verify_webhook_signature(raw_body, x_hub_signature_256 or ""):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature")

    try:
        payload = await request.json()
    except Exception:
        return {"status": "ignored_non_json"}

    # 2. Parse payload
    parsed = WhatsAppPayloadParser.parse_payload(payload)

    # 3. Process each customer message
    for msg in parsed["messages"]:
        # Deduplication check
        if WhatsAppSecurity.is_duplicate_message(msg.message_id):
            logger.info(f"Ignored duplicate WhatsApp message ID: {msg.message_id}")
            continue

        # Execute full LangGraph orchestrator
        workflow_res = await process_whatsapp_message(
            sender_phone=msg.sender_phone,
            message_text=msg.message_text,
            referral_merchant_slug=msg.referral_slug
        )

        reply_text = workflow_res.get("response_text", "")
        if reply_text:
            # Deliver reply through WhatsApp Cloud API
            await WhatsAppCloudClient.send_text_message(
                recipient_phone=msg.sender_phone,
                message_text=reply_text
            )

    return {"status": "processed", "message_count": len(parsed["messages"])}

@router.post("/simulate")
async def simulate_message(req: SimulateMessageRequest):
    """
    Interactive WhatsApp simulation endpoint for dashboard live demo and automated tests.
    Executes the exact production LangGraph workflow without requiring active Meta webhooks.
    """
    res = await process_whatsapp_message(
        sender_phone=req.sender_phone,
        message_text=req.message_text,
        referral_merchant_slug=req.referral_merchant_slug
    )
    return res

@router.get("/simulator/outbound")
async def get_simulator_outbound():
    """Retrieve outbound simulated WhatsApp message delivery log."""
    return {"outbound_messages": SIMULATOR_OUTBOUND_MESSAGES[-50:]}
