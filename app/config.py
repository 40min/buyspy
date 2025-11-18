"""
Centralized application configuration.

This module provides type-safe access to all environment variables
using Pydantic Settings. Configuration is loaded from the .env file
and validated at application startup.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


@lru_cache()
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
    return Settings()