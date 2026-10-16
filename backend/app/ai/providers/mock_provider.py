from typing import Dict, Any, List, Optional
from backend.app.ai.providers.base import BaseAIProvider, AIResponse

class MockAIProvider(BaseAIProvider):
    """
    Intelligent deterministic offline mock AI provider for development and testing.
    Responds contextually based on message content, active merchant, and tool results.
    """

    def __init__(self, model_name: str = "mock-vera-engine"):
        super().__init__(model_name=model_name)

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> AIResponse:
        last_message = messages[-1].get("content", "").lower() if messages else ""

        # Context-based replies
        if "milk" in last_message:
            return AIResponse(
                content="At FreshMart Grocery, our Organic Whole Milk (1 Gallon) is $4.99 and currently in stock. Would you like me to place an order for delivery to your address?"
            )
        elif "kaju katli" in last_message:
            return AIResponse(
                content="Royal Sweets & Delights offers our signature handcrafted Premium Kaju Katli at $22.00/kg, and Stevia-sweetened Sugar-Free Kaju Katli at $24.00/kg. Would you like pickup or delivery, and shall I add festive gift packaging?"
            )
        elif "hair spa" in last_message or "haircut" in last_message or "salon" in last_message:
            return AIResponse(
                content="At Glow & Glamour Salon, our Signature Haircut & Blowout is $65.00 (60 mins) and Hydra-Glow Facial is $95.00. We have openings tomorrow with Master Stylist Elena at 10:00 AM, 11:30 AM, and 2:00 PM. Would you like to book one?"
            )
        elif "dental" in last_message or "cleaning" in last_message or "checkup" in last_message:
            return AIResponse(
                content="SmileCare Dental Clinic offers Comprehensive Exams & Cleanings for $120.00 and Teeth Whitening for $299.00. Dr. Vance has openings tomorrow at 9:00 AM and 10:30 AM. Would you like me to reserve a slot?"
            )
        elif "cancel" in last_message:
            return AIResponse(
                content="I can help you cancel your order or appointment. Please confirm your order number (e.g. GRO-1001) or booking reference (e.g. SLN-3001)."
            )
        elif any(w in last_message for w in ["hi", "hello", "hey"]):
            return AIResponse(
                content="Hello! I am Vera, your multi-merchant assistant. I can assist you with orders, pricing, and appointments for FreshMart Grocery, Royal Sweets, Glow Salon, or SmileCare Dental Clinic. How can I help you today?"
            )
        else:
            return AIResponse(
                content="I am here to assist you with our products, prices, offers, orders, and appointment bookings. Could you please specify which item or service you would like assistance with?"
            )

    async def test_connection(self) -> Dict[str, Any]:
        return {"connected": True, "provider": "MockAI (Development/Offline)", "model": self.model_name}
