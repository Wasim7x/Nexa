from typing import Optional
from backend.app.core.config import settings
from backend.app.ai.providers.base import BaseAIProvider
from backend.app.ai.providers.gemini_provider import GeminiProvider
from backend.app.ai.providers.openai_provider import OpenAIProvider
from backend.app.ai.providers.groq_provider import GroqProvider
from backend.app.ai.providers.ollama_provider import OllamaProvider
from backend.app.ai.providers.mock_provider import MockAIProvider

def get_ai_provider(provider_name: Optional[str] = None, model_name: Optional[str] = None) -> BaseAIProvider:
    """Factory to instantiate configured AI provider."""
    selected_provider = (provider_name or settings.AI_PROVIDER).lower()

    if selected_provider == "gemini":
        return GeminiProvider(
            model_name=model_name or settings.AI_MODEL,
            api_key=settings.GEMINI_API_KEY
        )
    elif selected_provider == "openai":
        return OpenAIProvider(
            model_name=model_name or "gpt-4o-mini",
            api_key=settings.OPENAI_API_KEY
        )
    elif selected_provider == "groq":
        return GroqProvider(
            model_name=model_name or "llama-3.3-70b-versatile",
            api_key=settings.GROQ_API_KEY
        )
    elif selected_provider == "ollama":
        return OllamaProvider(
            model_name=model_name or settings.OLLAMA_MODEL or settings.AI_MODEL or "qwen3:1.7b",
            base_url=settings.OLLAMA_BASE_URL
        )
    else:
        # Default mock provider
        return MockAIProvider()
