"""
Centralized application configuration.

This module provides type-safe access to all environment variables
using Pydantic Settings. Configuration is loaded from the .env file
and validated at application startup.
"""

import os
from functools import lru_cache

from pydantic import ConfigDict, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings are loaded from the .env file and validated using Pydantic.
    This ensures type safety and provides clear error messages if required
    settings are missing or invalid.
    """

    # Google Cloud settings
    gcp_project_id: str
    gcp_region: str = "europe-west1"

    # Telegram settings
    telegram_bot_token: str

    # Optional settings
    artifacts_bucket_name: str | None = None
    log_level: str = "INFO"

    @model_validator(mode="after")
    def validate_required_fields(self) -> "Settings":
        """Validate that required fields are not empty strings."""
        required_fields = ["gcp_project_id", "telegram_bot_token"]

        for field_name in required_fields:
            value = getattr(self, field_name)
            if not value or not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} cannot be empty")

        return self

    model_config = ConfigDict(  # type: ignore
        env_file=os.getenv("ENV_FILE", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    This function uses @lru_cache() to ensure Settings is instantiated
    only once (singleton pattern), improving performance and ensuring
    consistency across the application.

    Returns:
        Settings: The application settings instance

    Raises:
        ValidationError: If required environment variables are missing
                        or have invalid values
    """
    return Settings()  # type: ignore
