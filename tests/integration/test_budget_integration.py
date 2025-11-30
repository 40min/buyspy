# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# mypy: disable-error-code="arg-type,attr-defined,method-assign,union-attr"

"""Integration tests for budget enforcement in TelegramService."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from telegram import Chat, Message, Update, User
from telegram.ext import ContextTypes

from app.agent_engine_app import AgentEngineApp
from app.services.budget_service import BudgetService
from app.services.telegram_service import TelegramService


class AsyncGeneratorMock:
    """Mock async generator for testing."""

    def __init__(self, events: list[dict[str, Any]]) -> None:
        self.events = events
        self.index = 0

    def __aiter__(self) -> "AsyncGeneratorMock":
        return self

    async def __anext__(self) -> dict[str, Any]:
        if self.index < len(self.events):
            event = self.events[self.index]
            self.index += 1
            return event
        else:
            raise StopAsyncIteration


@pytest.fixture
async def redis_client():
    """Provide a Redis client for testing."""
    import fakeredis

    # Create a fake Redis instance
    redis_client = fakeredis.FakeRedis()
    yield redis_client
    # Clean up all keys after test
    await redis_client.flushall()


@pytest.fixture
async def budget_service(redis_client):
    """Provide a BudgetService instance for testing."""
    service = BudgetService(
        redis_client=redis_client,
        limit=3,  # Small limit for testing
        ttl=86400,
        whitelist=["whitelisted_user"],
    )
    yield service


@pytest.fixture
async def telegram_service(budget_service):
    """Provide a TelegramService instance for testing."""
    # Mock the agent engine
    mock_agent_engine = Mock(spec=AgentEngineApp)
    mock_agent_engine.logger = MagicMock()
    mock_agent_engine.register_feedback = Mock()

    service = TelegramService(
        bot_token="test-bot-token-456",
        agent_engine=mock_agent_engine,
        budget_service=budget_service,
    )
    yield service


@pytest.fixture
def mock_update_factory():
    """Factory to create mock Telegram Update objects."""

    def _create_update(message_text: str, chat_id: int, user_id: int) -> Update:
        update = Mock(spec=Update)

        # Mock the message
        update.message = Mock(spec=Message)
        update.message.text = message_text
        update.message.reply_text = AsyncMock()
        update.message.reply_markdown_v2 = AsyncMock()

        # Mock effective_chat
        update.effective_chat = Mock(spec=Chat)
        update.effective_chat.id = chat_id

        # Mock effective_user
        update.effective_user = Mock(spec=User)
        update.effective_user.id = user_id

        return update

    return _create_update


@pytest.fixture
def mock_context():
    """Create a mock context object."""
    context = Mock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot = Mock()
    context.bot.send_chat_action = AsyncMock()
    return context


@pytest.mark.asyncio
async def test_message_processed_under_limit(
    telegram_service: TelegramService,
    mock_update_factory,
    mock_context,
) -> None:
    """
    Test that messages are processed when user is under the budget limit.

    Verifies that messages under the limit are processed normally,
    budget counter increments, and agent engine is called.
    """
    # Create test message
    test_message = "What is the weather like today?"
    chat_id = 12345
    user_id = 67890
    update = mock_update_factory(test_message, chat_id, user_id)

    # Mock agent engine response
    mock_events = [
        {
            "author": "assistant",
            "content": {"parts": [{"text": "Sunny weather today!"}]},
        }
    ]
    telegram_service.agent_engine.async_stream_query = Mock(
        return_value=AsyncGeneratorMock(mock_events)
    )

    # Execute the integration flow
    await telegram_service.handle_message(update, mock_context)

    # Verify agent engine was called (message processed)
    telegram_service.agent_engine.async_stream_query.assert_called_once_with(
        message=test_message, user_id=str(user_id), session_id=str(chat_id)
    )

    # Verify typing action was sent
    mock_context.bot.send_chat_action.assert_called_once_with(
        chat_id=chat_id, action="typing"
    )

    # Verify response was sent back to user
    update.message.reply_markdown_v2.assert_called_once()

    # Verify budget counter incremented (should be 1 after first message)
    count = await telegram_service.budget_service.get_user_budget_count(str(user_id))
    assert count == 1


@pytest.mark.asyncio
async def test_message_rejected_over_limit(
    telegram_service: TelegramService,
    mock_update_factory,
    mock_context,
) -> None:
    """
    Test that messages are rejected when user exceeds the budget limit.

    Verifies that over-limit messages are rejected with appropriate message,
    no agent processing occurs, and user gets budget limit warning.
    """
    chat_id = 12345
    user_id = 67890

    # Send messages up to the limit (3 messages)
    for i in range(3):
        update = mock_update_factory(f"Message {i+1}", chat_id, user_id)
        mock_events = [
            {
                "author": "assistant",
                "content": {"parts": [{"text": f"Response {i+1}"}]},
            }
        ]
        telegram_service.agent_engine.async_stream_query = Mock(
            return_value=AsyncGeneratorMock(mock_events)
        )
        await telegram_service.handle_message(update, mock_context)

    # Verify counter is at limit
    count = await telegram_service.budget_service.get_user_budget_count(str(user_id))
    assert count == 3

    # Now send one more message (should be rejected)
    update = mock_update_factory("This should be rejected", chat_id, user_id)
    await telegram_service.handle_message(update, mock_context)

    # Verify agent engine was NOT called for the rejected message
    # (It was called 3 times before, should still be 3)
    assert telegram_service.agent_engine.async_stream_query.call_count == 3

    # Verify budget limit message was sent
    update.message.reply_text.assert_called_with(
        "⚠️ You've reached your daily message limit. Please try again in 24 hours."
    )

    # Verify no typing action for rejected message
    # (Should have been called 3 times before)
    assert mock_context.bot.send_chat_action.call_count == 3

    # Verify counter didn't increment beyond limit
    count = await telegram_service.budget_service.get_user_budget_count(str(user_id))
    assert count == 3


@pytest.mark.asyncio
async def test_whitelisted_user_bypasses_limit(
    telegram_service: TelegramService,
    mock_update_factory,
    mock_context,
) -> None:
    """
    Test that whitelisted users bypass the budget limit.

    Verifies that whitelisted users can send unlimited messages
    without hitting the budget limit.
    """
    chat_id = 12345
    user_id = 99999  # whitelisted_user from fixture

    # Send many messages (way over the limit)
    for i in range(10):
        update = mock_update_factory(f"Message {i+1}", chat_id, user_id)
        mock_events = [
            {
                "author": "assistant",
                "content": {"parts": [{"text": f"Response {i+1}"}]},
            }
        ]
        telegram_service.agent_engine.async_stream_query = Mock(
            return_value=AsyncGeneratorMock(mock_events)
        )
        await telegram_service.handle_message(update, mock_context)

    # Verify all messages were processed (agent engine called 10 times)
    assert telegram_service.agent_engine.async_stream_query.call_count == 10

    # Verify budget counter was not incremented (should be 0 for whitelisted)
    count = await telegram_service.budget_service.get_user_budget_count(str(user_id))
    assert count == 0

    # Verify typing actions were sent for all messages
    assert mock_context.bot.send_chat_action.call_count == 10


@pytest.mark.asyncio
async def test_budget_counter_increments_correctly(
    telegram_service: TelegramService,
    mock_update_factory,
    mock_context,
) -> None:
    """
    Test that the budget counter increments correctly with each message.

    Verifies counter starts at 0, increments by 1 each time,
    and maintains correct count throughout the session.
    """
    chat_id = 12345
    user_id = 67890

    # Initially should be 0
    count = await telegram_service.budget_service.get_user_budget_count(str(user_id))
    assert count == 0

    # Send first message
    update = mock_update_factory("First message", chat_id, user_id)
    mock_events = [
        {
            "author": "assistant",
            "content": {"parts": [{"text": "First response"}]},
        }
    ]
    telegram_service.agent_engine.async_stream_query = Mock(
        return_value=AsyncGeneratorMock(mock_events)
    )
    await telegram_service.handle_message(update, mock_context)

    count = await telegram_service.budget_service.get_user_budget_count(str(user_id))
    assert count == 1

    # Send second message
    update = mock_update_factory("Second message", chat_id, user_id)
    mock_events = [
        {
            "author": "assistant",
            "content": {"parts": [{"text": "Second response"}]},
        }
    ]
    telegram_service.agent_engine.async_stream_query = Mock(
        return_value=AsyncGeneratorMock(mock_events)
    )
    await telegram_service.handle_message(update, mock_context)

    count = await telegram_service.budget_service.get_user_budget_count(str(user_id))
    assert count == 2

    # Send third message
    update = mock_update_factory("Third message", chat_id, user_id)
    mock_events = [
        {
            "author": "assistant",
            "content": {"parts": [{"text": "Third response"}]},
        }
    ]
    telegram_service.agent_engine.async_stream_query = Mock(
        return_value=AsyncGeneratorMock(mock_events)
    )
    await telegram_service.handle_message(update, mock_context)

    count = await telegram_service.budget_service.get_user_budget_count(str(user_id))
    assert count == 3


@pytest.mark.asyncio
async def test_ttl_set_on_first_message(
    telegram_service: TelegramService,
    mock_update_factory,
    mock_context,
) -> None:
    """
    Test that TTL is set on the Redis key when the first message is sent.

    Verifies that the first message sets up the TTL correctly,
    and subsequent messages don't reset it.
    """
    chat_id = 12345
    user_id = 67890

    # Before any messages, key should not exist or have no TTL
    redis_client = telegram_service.budget_service.redis_client
    key = f"budget:{user_id}"

    # Send first message
    update = mock_update_factory("First message", chat_id, user_id)
    mock_events = [
        {
            "author": "assistant",
            "content": {"parts": [{"text": "First response"}]},
        }
    ]
    telegram_service.agent_engine.async_stream_query = Mock(
        return_value=AsyncGeneratorMock(mock_events)
    )
    await telegram_service.handle_message(update, mock_context)

    # Check that TTL is set (should be close to 86400 seconds)
    ttl = await redis_client.ttl(key)
    assert 86300 <= ttl <= 86400  # Allow some margin for test execution time

    # Send second message
    update = mock_update_factory("Second message", chat_id, user_id)
    mock_events = [
        {
            "author": "assistant",
            "content": {"parts": [{"text": "Second response"}]},
        }
    ]
    telegram_service.agent_engine.async_stream_query = Mock(
        return_value=AsyncGeneratorMock(mock_events)
    )
    await telegram_service.handle_message(update, mock_context)

    # TTL should still be set and slightly decreased
    ttl_after = await redis_client.ttl(key)
    assert 86000 <= ttl_after <= 86300  # Should be less than original but still high

    # Verify counter incremented correctly
    count = await telegram_service.budget_service.get_user_budget_count(str(user_id))
    assert count == 2


@pytest.mark.asyncio
async def test_budget_reset_functionality(
    telegram_service: TelegramService,
    mock_update_factory,
    mock_context,
) -> None:
    """
    Test that budget can be reset and new messages work after reset.

    Verifies the reset functionality works and allows new messages.
    """
    chat_id = 12345
    user_id = 67890

    # Send a couple messages to increment counter
    for i in range(2):
        update = mock_update_factory(f"Message {i+1}", chat_id, user_id)
        mock_events = [
            {
                "author": "assistant",
                "content": {"parts": [{"text": f"Response {i+1}"}]},
            }
        ]
        telegram_service.agent_engine.async_stream_query = Mock(
            return_value=AsyncGeneratorMock(mock_events)
        )
        await telegram_service.handle_message(update, mock_context)

    # Verify counter is at 2
    count = await telegram_service.budget_service.get_user_budget_count(str(user_id))
    assert count == 2

    # Reset budget
    reset_result = await telegram_service.budget_service.reset_user_budget(str(user_id))
    assert reset_result is True

    # Verify counter is reset to 0
    count = await telegram_service.budget_service.get_user_budget_count(str(user_id))
    assert count == 0

    # Send another message - should work
    update = mock_update_factory("After reset message", chat_id, user_id)
    mock_events = [
        {
            "author": "assistant",
            "content": {"parts": [{"text": "After reset response"}]},
        }
    ]
    telegram_service.agent_engine.async_stream_query = Mock(
        return_value=AsyncGeneratorMock(mock_events)
    )
    await telegram_service.handle_message(update, mock_context)

    # Verify it was processed and counter incremented to 1
    telegram_service.agent_engine.async_stream_query.assert_called_with(
        message="After reset message", user_id=str(user_id), session_id=str(chat_id)
    )
    count = await telegram_service.budget_service.get_user_budget_count(str(user_id))
    assert count == 1


@pytest.mark.asyncio
async def test_redis_connection_failure_fails_open(
    telegram_service: TelegramService,
    mock_update_factory,
    mock_context,
) -> None:
    """
    Test that Redis connection failures cause fail-open behavior.

    Verifies that when Redis is unavailable, messages are still processed
    (fail-open behavior for budget checks).
    """
    chat_id = 12345
    user_id = 67890

    # Mock Redis to raise exceptions
    original_incr = telegram_service.budget_service.redis_client.incr
    telegram_service.budget_service.redis_client.incr = AsyncMock(
        side_effect=Exception("Redis connection failed")
    )

    try:
        # Send message - should still be processed due to fail-open
        update = mock_update_factory("Test message", chat_id, user_id)
        mock_events = [
            {
                "author": "assistant",
                "content": {"parts": [{"text": "Test response"}]},
            }
        ]
        telegram_service.agent_engine.async_stream_query = Mock(
            return_value=AsyncGeneratorMock(mock_events)
        )
        await telegram_service.handle_message(update, mock_context)

        # Verify message was processed despite Redis failure
        telegram_service.agent_engine.async_stream_query.assert_called_once_with(
            message="Test message", user_id=str(user_id), session_id=str(chat_id)
        )

        # Verify response was sent
        update.message.reply_markdown_v2.assert_called_once()

    finally:
        # Restore original Redis client method

        telegram_service.budget_service.redis_client.incr = original_incr
