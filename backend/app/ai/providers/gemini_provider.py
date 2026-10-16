from typing import Dict, Any, List, Optional
import httpx
from backend.app.ai.providers.base import BaseAIProvider, AIResponse

class GeminiProvider(BaseAIProvider):
    """Google Gemini AI integration."""

    def __init__(self, model_name: str = "gemini-1.5-flash", api_key: Optional[str] = None):
        super().__init__(model_name=model_name, api_key=api_key)

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> AIResponse:
        if not self.api_key:
            return AIResponse(content="[Gemini Provider Error: Missing GEMINI_API_KEY]")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        
        # Build contents structure
        contents = []
        for m in messages:
            role = "user" if m.get("role") in ["user", "customer"] else "model"
            contents.append({
                "role": role,
                "parts": [{"text": m.get("content", "")}]
            })

        payload: Dict[str, Any] = {"contents": contents}
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        return AIResponse(content=text)
                    return AIResponse(content="No response generated.")
                return AIResponse(content=f"Gemini API returned status {resp.status_code}: {resp.text}")
            except Exception as e:
                return AIResponse(content=f"Gemini request failed: {str(e)}")

    async def test_connection(self) -> Dict[str, Any]:
        if not self.api_key:
            return {"connected": False, "error": "GEMINI_API_KEY not configured"}

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}?key={self.api_key}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    return {"connected": True, "model": self.model_name, "provider": "Google Gemini"}
                return {"connected": False, "status_code": resp.status_code, "error": resp.text}
            except Exception as e:
                return {"connected": False, "error": str(e)}
