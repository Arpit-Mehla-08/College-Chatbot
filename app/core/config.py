"""Application configuration using pydantic-settings."""

from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./mock.db"

    # Metabase (alternative to direct DB)
    USE_METABASE: bool = False

    @field_validator("USE_METABASE", mode="before")
    @classmethod
    def parse_use_metabase(cls, v):
        """Convert string 'true'/'false' to boolean."""
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes")
        return bool(v)
    METABASE_URL: Optional[str] = None
    METABASE_USERNAME: Optional[str] = None
    METABASE_PASSWORD: Optional[str] = None
    METABASE_DATABASE_ID: int = 1

    # LLM Provider
    LLM_PROVIDER: str = "openai"

    # OpenAI-compatible endpoint config (used by LiteLLM / penpencil proxy)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "vertex_ai/gemini-2.5-pro"
    OPENAI_BASE_URL: str = "https://litellm-platform.penpencil.guru"

    # Backward compatibility for older Gemini-oriented env names
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "vertex_ai/gemini-2.5-pro"
    GEMINI_BASE_URL: str = "https://litellm-platform.penpencil.guru"

    # Application
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    QUERY_LOG_FILE: str = "query_logs.json"

    # Week definition
    WEEK_DEFINITION: str = "calendar"  # "calendar" (Mon-Sun) or "rolling7"

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 10

    # Query timeout in seconds
    QUERY_TIMEOUT_SECONDS: int = 10

    @property
    def is_sqlite(self) -> bool:
        return "sqlite" in self.DATABASE_URL

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
