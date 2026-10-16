import logging
from typing import Dict, Any, Optional, List
import httpx
from backend.app.core.config import settings

logger = logging.getLogger("vera.whatsapp")

# In-memory outbound log for simulator and verification
SIMULATOR_OUTBOUND_MESSAGES: List[Dict[str, Any]] = []

class WhatsAppCloudClient:
    """Official Meta WhatsApp Business Cloud API Client."""

    @classmethod
    async def send_text_message(
        cls,
        recipient_phone: str,
        message_text: str,
        preview_url: bool = False
    ) -> Dict[str, Any]:
        """Send a WhatsApp text message to a customer."""
        clean_recipient = recipient_phone.replace("+", "").strip()

        # If using mock simulator or credentials are not configured
        if settings.USE_MOCK_WHATSAPP or not settings.WHATSAPP_ACCESS_TOKEN or not settings.WHATSAPP_PHONE_NUMBER_ID:
            simulated_response = {
                "messaging_product": "whatsapp",
                "contacts": [{"input": recipient_phone, "wa_id": clean_recipient}],
                "messages": [{"id": f"wamid.simulated.{len(SIMULATOR_OUTBOUND_MESSAGES) + 1}"}],
                "status": "simulated_delivered",
                "recipient": recipient_phone,
                "text": message_text
            }
            SIMULATOR_OUTBOUND_MESSAGES.append(simulated_response)
            logger.info(f"[Mock WhatsApp] Sent to {recipient_phone}: {message_text[:80]}...")
            return simulated_response

        # Official Meta Cloud API Call
        url = f"https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": clean_recipient,
            "type": "text",
            "text": {
                "preview_url": preview_url,
                "body": message_text
            }
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code in [200, 201]:
                    return resp.json()
                logger.error(f"Meta WhatsApp API error {resp.status_code}: {resp.text}")
                return {"error": resp.text, "status_code": resp.status_code}
            except Exception as e:
                logger.error(f"Failed to deliver WhatsApp message: {e}")
                return {"error": str(e)}

    @classmethod
    async def send_template_message(
        cls,
        recipient_phone: str,
        template_name: str,
        language_code: str = "en_US",
        components: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Send a pre-approved Meta WhatsApp Business template message."""
        clean_recipient = recipient_phone.replace("+", "").strip()

        if settings.USE_MOCK_WHATSAPP or not settings.WHATSAPP_ACCESS_TOKEN:
            sim_res = {
                "messaging_product": "whatsapp",
                "contacts": [{"input": recipient_phone, "wa_id": clean_recipient}],
                "messages": [{"id": f"wamid.simulated_template.{template_name}"}],
                "status": "simulated_delivered",
                "template": template_name
            }
            SIMULATOR_OUTBOUND_MESSAGES.append(sim_res)
            return sim_res

        url = f"https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": clean_recipient,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
                "components": components or []
            }
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.post(url, headers=headers, json=payload)
                return resp.json() if resp.status_code in [200, 201] else {"error": resp.text}
            except Exception as e:
                return {"error": str(e)}
