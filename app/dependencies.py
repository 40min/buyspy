"""
Dependency injection functions.

This module provides individual getter functions for each dependency,
following proper dependency injection patterns. Each function returns
a single entity, making it easy to inject dependencies where needed.
"""

from redis import asyncio as redis_asyncio

from app.agent_engine_app import AgentEngineApp
from app.agent_engine_app import get_agent_engine as _get_agent_engine
from app.config import Settings, get_settings
from app.services.budget_service import BudgetService
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

    Returns the AgentEngineApp singleton that is lazily initialized
    when first called. This prevents expensive Google API calls during
    module import.

    Returns:
        AgentEngineApp: The singleton agent engine instance
    """
    return _get_agent_engine()


def get_redis_client() -> redis_asyncio.Redis:
    """
    Get Redis client instance.

    Returns:
        redis_asyncio.Redis: Redis client configured from settings
    """
    config = get_config()
    return redis_asyncio.Redis(
        host=config.redis_host,
        port=config.redis_port,
        decode_responses=True,
    )


def get_budget_service() -> BudgetService:
    """
    Get BudgetService instance.

    Returns:
        BudgetService: Budget service configured from settings
    """
    config = get_config()
    redis_client = get_redis_client()
    # Parse comma-separated whitelist into list
    whitelisted_users = [
        user.strip() for user in config.whitelisted_users.split(",") if user.strip()
    ]

    return BudgetService(
        redis_client=redis_client,
        limit=config.message_limit,
        ttl=config.message_limit_ttl,
        whitelist=whitelisted_users,
    )


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
    budget_service = get_budget_service()

    return TelegramService(
        bot_token=config.telegram_bot_token,
        agent_engine=engine,
        budget_service=budget_service,
        timeout_seconds=600,  # 10 minutes timeout for agent processing
    )
