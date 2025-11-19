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

import os
from collections.abc import AsyncIterator, Callable, Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from telegram import Chat, Message, Update, User
from telegram.ext import ContextTypes

from app.agent_engine_app import AgentEngineApp
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
def mock_telegram_api() -> Generator[dict[str, Any], None, None]:
    """Mock Telegram API calls to avoid network requests."""
    with (
        patch("telegram.Bot.send_message") as mock_send_message,
        patch("telegram.Bot.send_chat_action") as mock_send_chat_action,
        patch("telegram.ext.Application.builder") as mock_builder,
    ):
        # Setup Telegram API mocks
        mock_bot = MagicMock()
        mock_send_message.return_value = AsyncMock()
        mock_send_chat_action.return_value = AsyncMock()
        mock_bot.send_message = mock_send_message
        mock_bot.send_chat_action = mock_send_chat_action

        mock_application = MagicMock()
        mock_builder.return_value.token.return_value.build.return_value = (
            mock_application
        )

        yield {
            "bot": mock_bot,
            "send_message": mock_send_message,
            "send_chat_action": mock_send_chat_action,
            "application": mock_application,
            "builder": mock_builder,
        }


@pytest.fixture
def mock_google_apis() -> Generator[dict[str, Any], None, None]:
    """Mock Google API calls to avoid network requests."""
    with (
        patch("google.auth.default") as mock_auth,
        patch("vertexai.init") as mock_vertexai,
    ):
        # Setup Google API mocks
        mock_auth.return_value = (None, "test-project")
        mock_vertexai.return_value = None

        yield {
            "auth": mock_auth,
            "vertexai": mock_vertexai,
        }


@pytest.fixture
def mock_env_vars() -> Generator[dict[str, str], None, None]:
    """Set up test environment variables."""
    test_env = {
        "GOOGLE_CLOUD_PROJECT": "test-project-123",
        "GOOGLE_CLOUD_LOCATION": "europe-north1",
        "GOOGLE_GENAI_USE_VERTEXAI": "True",
        "ARTIFACTS_BUCKET_NAME": "test-bucket",
        "GCP_PROJECT_ID": "test-project-123",
        "TELEGRAM_BOT_TOKEN": "test-bot-token-456",
        "GCP_REGION": "europe-west1",
        "ENV_FILE": ".env.test",
    }

    # Store original values
    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value

    yield test_env

    # Restore original environment
    for key, original_value in original_env.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value


@pytest.fixture
def mock_update_factory() -> Callable[[str, int, int], Update]:
    """Factory to create mock Telegram Update objects."""

    def _create_update(message_text: str, chat_id: int, user_id: int) -> Update:
        update = Mock(spec=Update)

        # Mock the message
        update.message = Mock(spec=Message)
        update.message.text = message_text
        update.message.reply_text = AsyncMock()

        # Mock effective_chat
        update.effective_chat = Mock(spec=Chat)
        update.effective_chat.id = chat_id

        # Mock effective_user
        update.effective_user = Mock(spec=User)
        update.effective_user.id = user_id

        return update

    return _create_update


@pytest.fixture
def mock_context() -> ContextTypes.DEFAULT_TYPE:
    """Create a mock context object."""
    context = Mock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot = Mock()
    context.bot.send_chat_action = AsyncMock()
    return context


@pytest.fixture
def mock_agent_engine(mock_google_apis: dict[str, Any]) -> AgentEngineApp:
    """Create a mock AgentEngineApp for testing."""
    # Create a simple mock agent engine
    mock_engine = Mock(spec=AgentEngineApp)
    mock_engine.logger = MagicMock()
    mock_engine.register_feedback = Mock()
    return mock_engine


@pytest.fixture
def telegram_service(mock_agent_engine: AgentEngineApp) -> TelegramService:
    """Create a TelegramService instance for testing."""
    return TelegramService(
        bot_token="test-bot-token-456",
        agent_engine=mock_agent_engine,
    )


@pytest.mark.asyncio
async def test_end_to_end_message_flow_success(
    telegram_service: TelegramService,
    mock_update_factory: Callable[[str, int, int], Update],
    mock_context: ContextTypes.DEFAULT_TYPE,
    mock_telegram_api: dict[str, Any],
) -> None:
    """
    Integration test for successful end-to-end message flow.

    Tests: Telegram Update → TelegramService → AgentEngineApp → Response
    """
    # Create test message
    test_message = "What is the weather like today?"
    chat_id = 12345
    user_id = 67890
    update = mock_update_factory(test_message, chat_id, user_id)

    # Mock agent engine response with realistic event structure
    mock_events = [
        {
            "author": "assistant",
            "content": {
                "parts": [{"text": "I can help you with weather information. "}]
            },
        },
        {
            "author": "assistant",
            "content": {
                "parts": [
                    {"text": "The current weather is sunny with a temperature of 22°C."}
                ]
            },
        },
    ]

    # Patch the agent engine's async_stream_query method
    telegram_service.agent_engine.async_stream_query = Mock(
        return_value=AsyncGeneratorMock(mock_events)
    )

    # Execute the integration flow
    await telegram_service.handle_message(update, mock_context)

    # Verify agent engine was called with correct parameters
    telegram_service.agent_engine.async_stream_query.assert_called_once_with(
        message=test_message, user_id=str(user_id)
    )

    # Verify typing action was sent
    mock_context.bot.send_chat_action.assert_called_once_with(
        chat_id=chat_id, action="typing"
    )

    # Verify response was sent back to user
    update.message.reply_text.assert_called_once_with(
        "I can help you with weather information. The current weather is sunny with a temperature of 22°C."
    )


@pytest.mark.asyncio
async def test_async_message_handling_realistic_scenario(
    telegram_service: TelegramService,
    mock_update_factory: Callable[[str, int, int], Update],
    mock_context: ContextTypes.DEFAULT_TYPE,
    mock_telegram_api: dict[str, Any],
) -> None:
    """
    Integration test for async message handling in realistic scenario.

    Tests that the service properly handles multiple events from the agent engine
    and concatenates them correctly.
    """
    # Create test message with realistic conversation
    test_message = "Can you help me plan my shopping?"
    chat_id = 12345
    user_id = 67890
    update = mock_update_factory(test_message, chat_id, user_id)

    # Mock agent engine response with multiple events (realistic streaming)
    mock_events = [
        {
            "author": "assistant",
            "content": {
                "parts": [{"text": "I'd be happy to help you plan your shopping! "}]
            },
        },
        {
            "author": "assistant",
            "content": {
                "parts": [{"text": "What kind of items are you looking to buy? "}]
            },
        },
        {
            "author": "assistant",
            "content": {
                "parts": [
                    {"text": "I can suggest stores and help you find the best deals."}
                ]
            },
        },
    ]

    # Patch the agent engine's async_stream_query method
    telegram_service.agent_engine.async_stream_query = Mock(
        return_value=AsyncGeneratorMock(mock_events)
    )

    # Execute the integration flow
    await telegram_service.handle_message(update, mock_context)

    # Verify the complete response was concatenated correctly
    expected_response = (
        "I'd be happy to help you plan your shopping! "
        "What kind of items are you looking to buy? "
        "I can suggest stores and help you find the best deals."
    )
    update.message.reply_text.assert_called_once_with(expected_response)


@pytest.mark.asyncio
async def test_service_integration_with_agent_engine_app(
    telegram_service: TelegramService,
    mock_agent_engine: AgentEngineApp,
    mock_update_factory: Callable[[str, int, int], Update],
    mock_context: ContextTypes.DEFAULT_TYPE,
    mock_telegram_api: dict[str, Any],
) -> None:
    """
    Integration test for service properly integrating with AgentEngineApp.

    Tests that the TelegramService correctly uses the AgentEngineApp instance
    and that feedback registration works properly.
    """
    # Verify service has the correct agent engine instance
    assert telegram_service.agent_engine is mock_agent_engine

    # Create test message
    test_message = "Test integration"
    chat_id = 12345
    user_id = 67890
    update = mock_update_factory(test_message, chat_id, user_id)

    # Mock agent engine response
    mock_events = [
        {
            "author": "assistant",
            "content": {"parts": [{"text": "Integration test response"}]},
        }
    ]

    # Patch the agent engine's async_stream_query method
    telegram_service.agent_engine.async_stream_query = Mock(
        return_value=AsyncGeneratorMock(mock_events)
    )

    # Execute the integration flow
    await telegram_service.handle_message(update, mock_context)

    # Verify agent engine integration worked correctly
    telegram_service.agent_engine.async_stream_query.assert_called_once_with(
        message=test_message, user_id=str(user_id)
    )

    # Test feedback registration integration
    feedback_data = {
        "score": 5,
        "text": "Great response!",
        "invocation_id": "integration-test-123",
    }

    # Verify register_feedback method exists and can be called
    assert hasattr(mock_agent_engine, "register_feedback")
    try:
        mock_agent_engine.register_feedback(feedback_data)
    except Exception as e:
        pytest.fail(f"register_feedback raised an exception: {e}")


@pytest.mark.asyncio
async def test_error_recovery_and_resilience(
    telegram_service: TelegramService,
    mock_update_factory: Callable[[str, int, int], Update],
    mock_context: ContextTypes.DEFAULT_TYPE,
    mock_telegram_api: dict[str, Any],
) -> None:
    """
    Integration test for error recovery and resilience.

    Tests that the service handles various error conditions gracefully
    and provides appropriate fallback responses.
    """
    # Test case 1: Agent engine returns empty response
    test_message = "Test empty response"
    chat_id = 12345
    user_id = 67890
    update = mock_update_factory(test_message, chat_id, user_id)

    # Mock agent engine to return empty events
    telegram_service.agent_engine.async_stream_query = Mock(
        return_value=AsyncGeneratorMock([])
    )

    await telegram_service.handle_message(update, mock_context)

    # Verify fallback error message was sent
    update.message.reply_text.assert_called_once_with(
        "I apologize, but I couldn't generate a response. Please try again."
    )

    # Test case 2: Agent engine raises exception
    test_message = "Test exception handling"
    chat_id = 12346
    user_id = 67891
    update = mock_update_factory(test_message, chat_id, user_id)

    # Mock agent engine to raise exception
    async def mock_exception_stream(
        message: str, user_id: str
    ) -> AsyncIterator[dict[str, Any]]:
        raise Exception("Agent engine error")

    telegram_service.agent_engine.async_stream_query = Mock(
        side_effect=mock_exception_stream
    )

    await telegram_service.handle_message(update, mock_context)

    # Verify user-friendly error message was sent
    update.message.reply_text.assert_called_once_with(
        "I apologize, but I encountered an error processing your message. Please try again in a moment."
    )


@pytest.mark.asyncio
async def test_graceful_shutdown_behavior(
    telegram_service: TelegramService,
    mock_telegram_api: dict[str, Any],
) -> None:
    """
    Integration test for graceful shutdown behavior.

    Tests that the service can be stopped gracefully without errors.
    """
    # Set up mock application
    mock_application = MagicMock()
    mock_application.stop = AsyncMock()
    mock_application.shutdown = AsyncMock()
    telegram_service.application = mock_application

    # Test graceful stop
    await telegram_service.stop()

    # Verify proper shutdown sequence
    mock_application.stop.assert_called_once()
    mock_application.shutdown.assert_called_once()


@pytest.mark.asyncio
async def test_start_command_integration(
    telegram_service: TelegramService,
    mock_update_factory: Callable[[str, int, int], Update],
    mock_telegram_api: dict[str, Any],
) -> None:
    """
    Integration test for start command handling.

    Tests that the start command works correctly in the integration context.
    """
    # Create test update for start command
    chat_id = 12345
    user_id = 67890
    update = mock_update_factory("/start", chat_id, user_id)

    # Execute start command
    await telegram_service.start_command(update, Mock(spec=ContextTypes.DEFAULT_TYPE))

    # Verify welcome message was sent
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args[0][0]

    assert "Welcome to BuySpy AI Assistant!" in call_args
    assert "I'm here to help you" in call_args


@pytest.mark.asyncio
async def test_handler_setup_integration(
    telegram_service: TelegramService,
    mock_telegram_api: dict[str, Any],
) -> None:
    """
    Integration test for handler setup.

    Tests that handlers are set up correctly in the integration context.
    """
    # Set up mock application
    mock_application = MagicMock()
    mock_application.add_handler = Mock()
    telegram_service.application = mock_application

    # Execute handler setup
    telegram_service.setup_handlers()

    # Verify handlers were added correctly
    assert mock_application.add_handler.call_count == 2


@pytest.mark.asyncio
async def test_message_validation_integration(
    telegram_service: TelegramService,
    mock_context: ContextTypes.DEFAULT_TYPE,
    mock_telegram_api: dict[str, Any],
) -> None:
    """
    Integration test for message validation.

    Tests that invalid messages are handled gracefully without processing.
    """
    # Test case 1: Missing message
    update = Mock(spec=Update)
    update.message = None
    update.effective_chat = Mock()
    update.effective_chat.id = 12345
    update.effective_user = Mock()
    update.effective_user.id = 67890

    await telegram_service.handle_message(update, mock_context)

    # Verify no processing occurred
    mock_context.bot.send_chat_action.assert_not_called()

    # Test case 2: Empty text message
    update = Mock(spec=Update)
    update.message = Mock(spec=Message)
    update.message.text = ""
    update.message.reply_text = AsyncMock()
    update.effective_chat = Mock()
    update.effective_chat.id = 12345
    update.effective_user = Mock()
    update.effective_user.id = 67890

    await telegram_service.handle_message(update, mock_context)

    # Verify no processing occurred
    mock_context.bot.send_chat_action.assert_not_called()


@pytest.mark.asyncio
async def test_long_message_handling_integration(
    telegram_service: TelegramService,
    mock_update_factory: Callable[[str, int, int], Update],
    mock_context: ContextTypes.DEFAULT_TYPE,
    mock_telegram_api: dict[str, Any],
) -> None:
    """
    Integration test for long message handling.

    Tests that long messages are handled correctly with proper logging.
    """
    # Create a long test message
    long_message = "A" * 200 + " What can you tell me about this?"
    chat_id = 12345
    user_id = 67890
    update = mock_update_factory(long_message, chat_id, user_id)

    # Mock agent engine response
    mock_events = [
        {
            "author": "assistant",
            "content": {
                "parts": [
                    {
                        "text": "I received your long message and can process it correctly."
                    }
                ]
            },
        }
    ]

    # Capture log messages to verify proper logging
    with patch.object(telegram_service.logger, "info") as mock_logger:
        telegram_service.agent_engine.async_stream_query = Mock(
            return_value=AsyncGeneratorMock(mock_events)
        )

        await telegram_service.handle_message(update, mock_context)

        # Verify response was sent despite long message
        update.message.reply_text.assert_called_once()

        # Verify logging occurred (incoming message should be logged)
        mock_logger.assert_called()
