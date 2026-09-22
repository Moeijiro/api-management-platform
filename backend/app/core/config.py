"""Application configuration, read from the environment or a local .env file."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"), env_file_encoding="utf-8", extra="ignore"
    )

    # --- Runtime ---------------------------------------------------------
    environment: Literal["development", "production"] = "development"
    frontend_url: str = "http://localhost:5173"
    public_api_url: str = "http://localhost:8000"

    # --- Database --------------------------------------------------------
    database_url: str = "sqlite:///./api_platform.db"

    # --- Security --------------------------------------------------------
    secret_key: str = Field(default="dev-only-insecure-secret", min_length=8)
    access_token_ttl_minutes: int = Field(default=720, ge=5)
    cookie_secure: bool = False
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    allow_registration: bool = True

    # --- API keys --------------------------------------------------------
    api_key_prefix: str = Field(default="dev_live", pattern=r"^[a-z][a-z0-9_]{2,15}$")
    default_rate_limit_per_minute: int = Field(default=60, ge=1, le=100_000)
    max_keys_per_user: int = Field(default=10, ge=1, le=100)

    # --- Request logging --------------------------------------------------
    log_flush_interval_seconds: float = Field(default=0.5, gt=0, le=10)
    log_batch_size: int = Field(default=100, ge=1, le=10_000)
    log_retention_days: int = Field(default=30, ge=0)
    log_client_ip: bool = True

    @field_validator("frontend_url", "public_api_url")
    @classmethod
    def _strip_slash(cls, value: str) -> str:
        return value.rstrip("/")

    @model_validator(mode="after")
    def _guard_production(self) -> "Settings":
        """Refuse to boot with a configuration that is unsafe in production."""
        if self.environment == "production":
            if "insecure" in self.secret_key or len(self.secret_key) < 32:
                raise ValueError("SECRET_KEY must be a strong value in production")
            if not self.cookie_secure:
                raise ValueError("COOKIE_SECURE must be true in production")
        return self

    @property
    def cors_origins(self) -> list[str]:
        return [self.frontend_url]

    @property
    def debug_errors(self) -> bool:
        """Whether an unexpected error may reveal its type to the client."""
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
