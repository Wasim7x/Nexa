from typing import Dict, Any, Optional, List
from pydantic import BaseModel

class ParsedIncomingMessage(BaseModel):
    message_id: str
    sender_phone: str
    message_text: str
    message_type: str = "text"
    referral_slug: Optional[str] = None
    timestamp: Optional[str] = None

class ParsedStatusUpdate(BaseModel):
    message_id: str
    recipient_phone: str
    status: str  # 'sent', 'delivered', 'read', 'failed'
    timestamp: Optional[str] = None

class WhatsAppPayloadParser:
    """Parses standard Meta WhatsApp Business Cloud API webhook payloads."""

    @classmethod
    def parse_payload(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts incoming customer messages or status updates.
        Returns: {"messages": List[ParsedIncomingMessage], "statuses": List[ParsedStatusUpdate]}
        """
        parsed_messages: List[ParsedIncomingMessage] = []
        parsed_statuses: List[ParsedStatusUpdate] = []

        entries = data.get("entry", [])
        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                val = change.get("value", {})
                
                # 1. Parse incoming customer messages
                raw_msgs = val.get("messages", [])
                for rm in raw_msgs:
                    m_id = rm.get("id")
                    from_phone = rm.get("from")
                    m_type = rm.get("type", "text")
                    text_body = ""

                    if m_type == "text":
                        text_body = rm.get("text", {}).get("body", "")
                    elif m_type == "button":
                        text_body = rm.get("button", {}).get("text", "")
                    elif m_type == "interactive":
                        interactive = rm.get("interactive", {})
                        if interactive.get("type") == "button_reply":
                            text_body = interactive.get("button_reply", {}).get("title", "")
                        elif interactive.get("type") == "list_reply":
                            text_body = interactive.get("list_reply", {}).get("title", "")

                    # Extract referral parameter (e.g. from Click-to-WhatsApp ads or links)
                    referral_slug = None
                    referral = rm.get("referral", {})
                    if referral:
                        ref_url = referral.get("source_url", "")
                        if "grocery" in ref_url.lower():
                            referral_slug = "grocery"
                        elif "sweets" in ref_url.lower():
                            referral_slug = "sweets"
                        elif "salon" in ref_url.lower():
                            referral_slug = "salon"
                        elif "dental" in ref_url.lower():
                            referral_slug = "dental"

                    if m_id and from_phone and text_body:
                        # Normalize phone prefix
                        if not from_phone.startswith("+"):
                            from_phone = "+" + from_phone

                        parsed_messages.append(ParsedIncomingMessage(
                            message_id=m_id,
                            sender_phone=from_phone,
                            message_text=text_body,
                            message_type=m_type,
                            referral_slug=referral_slug,
                            timestamp=rm.get("timestamp")
                        ))

                # 2. Parse delivery status updates
                raw_statuses = val.get("statuses", [])
                for rs in raw_statuses:
                    s_id = rs.get("id")
                    recipient = rs.get("recipient_id")
                    status = rs.get("status")
                    if s_id and status:
                        parsed_statuses.append(ParsedStatusUpdate(
                            message_id=s_id,
                            recipient_phone=recipient or "",
                            status=status,
                            timestamp=rs.get("timestamp")
                        ))

        return {
            "messages": parsed_messages,
            "statuses": parsed_statuses
        }
