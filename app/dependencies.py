"""
Dependency injection functions.

This module provides individual getter functions for each dependency,
following proper dependency injection patterns. Each function returns
a single entity, making it easy to inject dependencies where needed.
"""

from app.agent_engine_app import AgentEngineApp, agent_engine
from app.config import Settings, get_settings
from app.services.telegram_service import TelegramService


def get_config() -> Settings:
    """
    Get application configuration.

    Returns the cached Settings instance containing all application
    configuration loaded from environment variables.

    Note: Caching is handled by get_settings() in app.config,
    so no additional caching is needed here.

    Returns:
        Settings: The application settings instance
    """
    return get_settings()


def get_agent_engine() -> AgentEngineApp:
    """
    Get the singleton agent engine instance.

    Returns the AgentEngineApp singleton that is initialized at module
    level in app/agent_engine_app.py. This is the core agent that processes
    user messages.

    Returns:
        AgentEngineApp: The singleton agent engine instance
    """
    return agent_engine


def get_telegram_service() -> TelegramService:
    """
    Create and return TelegramService instance.

    This function demonstrates proper dependency injection:
    - Each dependency is obtained via its own getter function
    - Dependencies are injected into the service constructor
    - No tuples or multiple return values

    Returns:
        TelegramService: Configured Telegram service instance
    """
    config = get_config()
    engine = get_agent_engine()

    return TelegramService(bot_token=config.telegram_bot_token, agent_engine=engine)
