from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="CASEFLOW_",
        case_sensitive=False,
        extra="ignore",
    )

    environment: Literal["development", "test", "production"] = "development"
    database_url: str = "sqlite+aiosqlite:///./caseflow.db"
    api_key: str = ""
    openai_model: str = "gpt-5"
    max_case_bytes: int = Field(default=10_000_000, ge=1_000, le=50_000_000)
    max_case_characters: int = Field(default=250_000, ge=10_000)
    max_agent_turns: int = Field(default=12, ge=1, le=50)
    log_level: str = "INFO"
    enable_web_search: bool = True
    auto_create_schema: bool = True

    @model_validator(mode="after")
    def validate_production(self) -> "Settings":
        if self.environment == "production":
            if not self.api_key:
                raise ValueError("CASEFLOW_API_KEY is required in production")
            if self.auto_create_schema:
                raise ValueError(
                    "CASEFLOW_AUTO_CREATE_SCHEMA must be false in production; use Alembic"
                )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
