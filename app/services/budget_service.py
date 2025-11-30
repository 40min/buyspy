"""Budget service for Redis-based rate limiting of user messages."""

import logging
from typing import Any


class BudgetService:
    """Service for managing user message budgets using Redis rate limiting.

    This service implements atomic rate limiting to prevent users from exceeding
    their message quotas within a specified time window. Whitelisted users bypass
    these limits entirely.

    Note: All methods are async to integrate seamlessly with the async TelegramService.
    """

    def __init__(
        self,
        redis_client: Any,
        limit: int,
        ttl: int,
        whitelist: list[str],
    ):
        """Initialize the budget service.

        Args:
            redis_client: Redis client instance for storing budget counters
            limit: Maximum number of messages allowed in the time window
            ttl: Time-to-live in seconds for the budget counter
            whitelist: List of whitelisted user IDs that bypass the limit
        """
        self.redis_client = redis_client
        self.logger = logging.getLogger(__name__)

        # Use provided values
        self.limit = limit
        self.ttl = ttl
        self.whitelist = whitelist

    async def check_and_increment(self, user_id: str) -> bool:
        """Check if user has budget remaining and increment their counter.

        This method implements atomic rate limiting using Redis INCR and EXPIRE
        operations. If the user ID is whitelisted, they always get access.

        Args:
            user_id: The Telegram user ID as a string

        Returns:
            True if the user has budget remaining (or is whitelisted), False otherwise

        Raises:
            Exception: If Redis operations fail, propagates the error
        """
        # Check whitelist first - whitelisted users bypass limits
        if str(user_id) in self.whitelist:
            self.logger.info(f"User {user_id} is whitelisted - bypassing budget check")
            return True

        # Redis key format for budget tracking
        budget_key = f"budget:{user_id}"

        # Atomic INCR operation using aioredis
        current_count = await self.redis_client.incr(budget_key)

        # If this is the first increment (count == 1), set the TTL
        if current_count == 1:
            await self.redis_client.expire(budget_key, self.ttl)
            self.logger.debug(
                f"Set TTL for budget key {budget_key}: {self.ttl} seconds"
            )

        # Check if within limit
        if current_count <= self.limit:
            self.logger.debug(f"User {user_id} budget OK: {current_count}/{self.limit}")
            return True
        else:
            self.logger.warning(
                f"User {user_id} exceeded budget: {current_count}/{self.limit}"
            )
            return False

    async def reset_user_budget(self, user_id: str) -> bool:
        """Reset a user's budget counter (useful for testing or admin operations).

        Args:
            user_id: The Telegram user ID as a string

        Returns:
            True if reset was successful, False otherwise
        """
        try:
            budget_key = f"budget:{user_id}"
            result = await self.redis_client.delete(budget_key)

            if result:
                self.logger.info(f"Successfully reset budget for user {user_id}")
                return True
            else:
                self.logger.debug(f"No budget found to reset for user {user_id}")
                return False

        except Exception as e:
            self.logger.error(
                f"Error resetting budget for user {user_id}: {e}", exc_info=True
            )
            return False

    async def get_user_budget_count(self, user_id: str) -> int | None:
        """Get the current budget count for a user.

        Args:
            user_id: The Telegram user ID as a string

        Returns:
            Current count if available, None on error
        """
        try:
            budget_key = f"budget:{user_id}"
            count = await self.redis_client.get(budget_key)

            if count is not None:
                return int(count)
            else:
                return 0

        except Exception as e:
            self.logger.error(
                f"Error getting budget count for user {user_id}: {e}", exc_info=True
            )
            return None
