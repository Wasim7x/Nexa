import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "Nexa — Multi-Merchant AI Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"  # 'development' or 'production'

    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000"
    ]

    # Database Settings
    # Default to a local SQLite database for instant zero-dependency testing, but easily switched to PostgreSQL
    DATABASE_URL: str = "sqlite+aiosqlite:///./vera.db"
    DATABASE_ECHO: bool = False

    # Redis Settings
    REDIS_URL: str = "redis://localhost:6379/0"
    USE_IN_MEMORY_CACHE: bool = True  # Fallback when Redis is not reachable

    # Security & JWT
    SECRET_KEY: str = "vera-secret-key-super-secure-change-in-production-7x991z"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Meta WhatsApp Business Cloud API
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_BUSINESS_ACCOUNT_ID: str = ""
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_VERIFY_TOKEN: str = "nexa_whatsapp_verify_token_secure_2026"
    WHATSAPP_API_VERSION: str = "v21.0"
    WHATSAPP_APP_SECRET: str = ""
    USE_MOCK_WHATSAPP: bool = True  # When True, simulator and mock transport are active

    # Default AI Provider Configuration
    AI_PROVIDER: str = "ollama"  # 'gemini', 'openai', 'groq', 'ollama', 'mock'
    AI_MODEL: str = "qwen3:1.7b"
    OLLAMA_MODEL: str = "qwen3:1.7b"
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # Rate Limiting & Safety
    MAX_REQUESTS_PER_MINUTE: int = 30
    RATE_LIMIT_COOLDOWN_SECONDS: int = 60

settings = Settings()
