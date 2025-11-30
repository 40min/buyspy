"""Unit tests for Budget service module."""

import logging
from unittest.mock import AsyncMock, Mock

import pytest

from app.services.budget_service import BudgetService


class TestBudgetService:
    """Test suite for BudgetService class."""

    @pytest.fixture
    def mock_redis_client(self) -> Mock:
        """Create a mock Redis client."""
        client = Mock()
        # Make async methods return AsyncMock
        client.incr = AsyncMock()
        client.expire = AsyncMock()
        client.delete = AsyncMock()
        client.get = AsyncMock()
        return client

    @pytest.fixture
    def budget_service(self, mock_redis_client: Mock) -> BudgetService:
        """Create a BudgetService instance for testing."""
        return BudgetService(
            redis_client=mock_redis_client,
            limit=10,
            ttl=86400,
            whitelist=["whitelisted_user"],
        )

    @pytest.mark.asyncio
    async def test_check_and_increment_whitelisted_user(
        self, budget_service: BudgetService
    ) -> None:
        """Test that whitelisted users always return True."""
        result = await budget_service.check_and_increment("whitelisted_user")
        assert result is True

    @pytest.mark.asyncio
    async def test_check_and_increment_first_message(
        self, budget_service: BudgetService, mock_redis_client: Mock
    ) -> None:
        """Test first message increments counter and sets TTL."""
        mock_redis_client.incr.return_value = 1

        result = await budget_service.check_and_increment("user123")

        assert result is True
        mock_redis_client.incr.assert_called_once_with("budget:user123")
        mock_redis_client.expire.assert_called_once_with("budget:user123", 86400)

    @pytest.mark.asyncio
    async def test_check_and_increment_under_limit(
        self, budget_service: BudgetService, mock_redis_client: Mock
    ) -> None:
        """Test message under limit returns True."""
        mock_redis_client.incr.return_value = 5

        result = await budget_service.check_and_increment("user123")

        assert result is True
        mock_redis_client.incr.assert_called_once_with("budget:user123")
        mock_redis_client.expire.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_and_increment_at_limit(
        self, budget_service: BudgetService, mock_redis_client: Mock
    ) -> None:
        """Test message at limit returns True."""
        mock_redis_client.incr.return_value = 10

        result = await budget_service.check_and_increment("user123")

        assert result is True
        mock_redis_client.incr.assert_called_once_with("budget:user123")
        mock_redis_client.expire.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_and_increment_over_limit(
        self, budget_service: BudgetService, mock_redis_client: Mock
    ) -> None:
        """Test message over limit returns False."""
        mock_redis_client.incr.return_value = 11

        result = await budget_service.check_and_increment("user123")

        assert result is False
        mock_redis_client.incr.assert_called_once_with("budget:user123")
        mock_redis_client.expire.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_and_increment_error_raises_exception(
        self, budget_service: BudgetService, mock_redis_client: Mock
    ) -> None:
        """Test that errors raise exceptions instead of failing open."""
        mock_redis_client.incr.side_effect = Exception("Redis error")

        with pytest.raises(Exception, match="Redis error"):
            await budget_service.check_and_increment("user123")

    @pytest.mark.asyncio
    async def test_reset_user_budget_success(
        self, budget_service: BudgetService, mock_redis_client: Mock
    ) -> None:
        """Test successful budget reset."""
        mock_redis_client.delete.return_value = 1

        result = await budget_service.reset_user_budget("user123")

        assert result is True
        mock_redis_client.delete.assert_called_once_with("budget:user123")

    @pytest.mark.asyncio
    async def test_reset_user_budget_no_key(
        self, budget_service: BudgetService, mock_redis_client: Mock
    ) -> None:
        """Test reset when no budget key exists."""
        mock_redis_client.delete.return_value = 0

        result = await budget_service.reset_user_budget("user123")

        assert result is False
        mock_redis_client.delete.assert_called_once_with("budget:user123")

    @pytest.mark.asyncio
    async def test_reset_user_budget_error(
        self, budget_service: BudgetService, mock_redis_client: Mock
    ) -> None:
        """Test error handling in reset_user_budget."""
        mock_redis_client.delete.side_effect = Exception("Redis error")

        result = await budget_service.reset_user_budget("user123")

        assert result is False

    @pytest.mark.asyncio
    async def test_get_user_budget_count_existing(
        self, budget_service: BudgetService, mock_redis_client: Mock
    ) -> None:
        """Test getting existing budget count."""
        mock_redis_client.get.return_value = "5"

        result = await budget_service.get_user_budget_count("user123")

        assert result == 5
        mock_redis_client.get.assert_called_once_with("budget:user123")

    @pytest.mark.asyncio
    async def test_get_user_budget_count_none(
        self, budget_service: BudgetService, mock_redis_client: Mock
    ) -> None:
        """Test getting budget count when key doesn't exist."""
        mock_redis_client.get.return_value = None

        result = await budget_service.get_user_budget_count("user123")

        assert result == 0
        mock_redis_client.get.assert_called_once_with("budget:user123")

    @pytest.mark.asyncio
    async def test_get_user_budget_count_error(
        self, budget_service: BudgetService, mock_redis_client: Mock
    ) -> None:
        """Test error handling in get_user_budget_count."""
        mock_redis_client.get.side_effect = Exception("Redis error")

        result = await budget_service.get_user_budget_count("user123")

        assert result is None

    def test_initialization(self, mock_redis_client: Mock) -> None:
        """Test BudgetService initialization."""
        service = BudgetService(
            redis_client=mock_redis_client,
            limit=5,
            ttl=3600,
            whitelist=["user1", "user2"],
        )

        assert service.redis_client == mock_redis_client
        assert service.limit == 5
        assert service.ttl == 3600
        assert service.whitelist == ["user1", "user2"]
        assert isinstance(service.logger, logging.Logger)
