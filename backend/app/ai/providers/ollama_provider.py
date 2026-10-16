import json
from typing import Dict, Any, List, Optional
import httpx
from backend.app.ai.providers.base import BaseAIProvider, AIResponse
from backend.app.core.config import settings

class OllamaProvider(BaseAIProvider):
    """
    Local Ollama instance integration.
    Enforces strictly local inference with zero cloud LLM fallback.
    Supports tool calling and structured parameters.
    """

    def __init__(self, model_name: Optional[str] = None, base_url: Optional[str] = None):
        effective_model = model_name or settings.OLLAMA_MODEL or settings.AI_MODEL or "qwen3:1.7b"
        effective_base_url = base_url or settings.OLLAMA_BASE_URL or "http://localhost:11434"
        super().__init__(model_name=effective_model, base_url=effective_base_url)

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> AIResponse:
        url = f"{self.base_url}/api/chat"
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        payload: Dict[str, Any] = {
            "model": self.model_name,
            "messages": full_messages,
            "stream": False,
            "options": {
                "temperature": 0.2
            }
        }

        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    msg = data.get("message", {})
                    content = msg.get("content", "")
                    tool_calls = msg.get("tool_calls")
                    return AIResponse(
                        content=content or "",
                        tool_calls=tool_calls,
                        finish_reason=data.get("done_reason", "stop"),
                        usage={"total_duration": data.get("total_duration", 0)}
                    )
                return AIResponse(content=f"Ollama error {resp.status_code}: {resp.text}")
            except httpx.ConnectError:
                return AIResponse(content=f"Ollama connection error: Service unreachable at {self.base_url}")
            except httpx.TimeoutException:
                return AIResponse(content=f"Ollama timeout: Model '{self.model_name}' did not respond within timeout window.")
            except Exception as e:
                return AIResponse(content=f"Ollama execution failed: {str(e)}")

    async def test_connection(self) -> Dict[str, Any]:
        """
        Validates Ollama connection and checks if the configured model is installed locally.
        Rejects uninstalled or unavailable models.
        """
        url = f"{self.base_url}/api/tags"
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return {"connected": False, "error": f"Ollama HTTP error {resp.status_code}"}

                data = resp.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                
                # Check if model or model with :latest is present
                target = self.model_name.lower()
                matching = [m for m in models if m.lower() == target or m.lower().startswith(f"{target}:") or target.startswith(f"{m.lower()}:")]

                if not matching:
                    return {
                        "connected": False,
                        "error": f"Model '{self.model_name}' is not installed locally in Ollama. Installed models: {models}",
                        "installed_models": models
                    }

                return {
                    "connected": True,
                    "provider": "Ollama",
                    "model": matching[0],
                    "installed_models": models
                }
            except httpx.ConnectError:
                return {"connected": False, "error": f"Could not connect to Ollama at {self.base_url}"}
            except Exception as e:
                return {"connected": False, "error": f"Ollama health check failed: {str(e)}"}
