from typing import Dict, Any, List, Optional
import httpx
from backend.app.ai.providers.base import BaseAIProvider, AIResponse

class OpenAIProvider(BaseAIProvider):
    """OpenAI API integration."""

    def __init__(self, model_name: str = "gpt-4o-mini", api_key: Optional[str] = None):
        super().__init__(model_name=model_name, api_key=api_key)

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> AIResponse:
        if not self.api_key:
            return AIResponse(content="[OpenAI Provider Error: Missing OPENAI_API_KEY]")

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        payload = {
            "model": self.model_name,
            "messages": full_messages,
            "temperature": 0.2
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    choices = data.get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content", "")
                        return AIResponse(content=content)
                    return AIResponse(content="No response generated.")
                return AIResponse(content=f"OpenAI error {resp.status_code}: {resp.text}")
            except Exception as e:
                return AIResponse(content=f"OpenAI request failed: {str(e)}")

    async def test_connection(self) -> Dict[str, Any]:
        if not self.api_key:
            return {"connected": False, "error": "OPENAI_API_KEY not configured"}

        url = "https://api.openai.com/v1/models"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    return {"connected": True, "provider": "OpenAI", "model": self.model_name}
                return {"connected": False, "status_code": resp.status_code, "error": resp.text}
            except Exception as e:
                return {"connected": False, "error": str(e)}
