#!/usr/bin/env python3
"""
BuySpy Telegram Bot Entrypoint

This module serves as the main entrypoint for the BuySpy Telegram bot.
It uses dependency injection to initialize the agent engine and start
the Telegram polling service.
"""

import logging
import signal

from app.dependencies import get_config, get_telegram_service
from app.services.telegram_service import TelegramService

# Initialize configuration and logging
config = get_config()
logging.basicConfig(
    level=config.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Main entry point for the Telegram bot."""
    telegram_service: TelegramService | None = None

    def signal_handler(sig: int, frame: object) -> None:
        logger.info(f"Received signal {sig}, initiating graceful shutdown...")
        if telegram_service:
            telegram_service.stop()

    try:
        logger.info("Starting BuySpy Telegram Bot...")

        # Get service via dependency injection
        telegram_service = get_telegram_service()
        logger.info("Service initialized successfully")

        # Register signal handlers for SIGTERM and SIGINT
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, signal_handler)

        # Start the bot polling
        logger.info("Starting Telegram bot polling...")
        telegram_service.start_polling()

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise
    finally:
        # Ensure cleanup
        if telegram_service:
            logger.info("Cleaning up resources...")
            telegram_service.stop()
        logger.info("BuySpy Telegram Bot stopped")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.error(f"Application failed: {e}", exc_info=True)
        exit(1)
