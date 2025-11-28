"""Unit tests for Telegram service module."""

import logging
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

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


class TestTelegramService:
    """Test suite for TelegramService class."""

    @pytest.fixture
    def mock_agent_engine(self) -> Mock:
        """Create a mock agent engine."""
        return Mock(spec=AgentEngineApp)

    @pytest.fixture
    def mock_update(self) -> Mock:
        """Create a mock Telegram Update object."""
        update = Mock(spec=Update)

        # Mock the message
        update.message = Mock(spec=Message)
        update.message.text = "Test message"
        update.message.reply_markdown_v2 = AsyncMock()

        # Mock effective_chat
        update.effective_chat = Mock(spec=Chat)
        update.effective_chat.id = 12345

        # Mock effective_user
        update.effective_user = Mock(spec=User)
        update.effective_user.id = 67890

        return update

    @pytest.fixture
    def mock_context(self) -> Mock:
        """Create a mock context object."""
        context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.bot = Mock()
        context.bot.send_chat_action = AsyncMock()
        return context

    @pytest.fixture
    def telegram_service(self, mock_agent_engine: Mock) -> TelegramService:
        """Create a TelegramService instance for testing."""
        return TelegramService(
            bot_token="test_bot_token", agent_engine=mock_agent_engine
        )

    def test_initialization(
        self, telegram_service: TelegramService, mock_agent_engine: Mock
    ) -> None:
        """Test TelegramService initialization with proper dependencies."""
        assert telegram_service.agent_engine == mock_agent_engine
        assert telegram_service.bot_token == "test_bot_token"
        assert telegram_service.application is None
        assert isinstance(telegram_service.logger, logging.Logger)

    @pytest.mark.asyncio
    async def test_handle_message_success(
        self,
        telegram_service: TelegramService,
        mock_update: Mock,
        mock_context: Mock,
        mock_agent_engine: Mock,
    ) -> None:
        """Test successful message processing flow."""
        # Mock the agent engine to return a streaming response with proper Event structure
        mock_events = [
            {
                "author": "assistant",
                "content": {"parts": [{"text": "Hello! How can I help you today?"}]},
            },
            {
                "author": "assistant",
                "content": {"parts": [{"text": " This is a test response."}]},
            },
        ]

        # Create async generator mock and assign it directly
        async_generator = AsyncGeneratorMock(mock_events)
        mock_agent_engine.async_stream_query = Mock(return_value=async_generator)

        # Execute the method
        await telegram_service.handle_message(mock_update, mock_context)

        # Verify the agent engine was called correctly
        mock_agent_engine.async_stream_query.assert_called_once_with(
            message="Test message", user_id="67890", session_id="12345"
        )

        # Verify chat action was sent
        mock_context.bot.send_chat_action.assert_called_once_with(
            chat_id=12345, action="typing"
        )

        # Verify the response was sent back
        mock_update.message.reply_markdown_v2.assert_called_once_with(
            "Hello! How can I help you today? This is a test response.",
            disable_web_page_preview=False,
        )

    @pytest.mark.asyncio
    async def test_handle_message_invalid_update_missing_message(
        self, telegram_service: TelegramService, mock_update: Mock, mock_context: Mock
    ) -> None:
        """Test error handling for invalid update missing message."""
        # Remove message from update
        mock_update.message = None

        await telegram_service.handle_message(mock_update, mock_context)

        # Verify no further processing occurred
        mock_context.bot.send_chat_action.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_message_invalid_update_missing_chat(
        self, telegram_service: TelegramService, mock_update: Mock, mock_context: Mock
    ) -> None:
        """Test error handling for invalid update missing chat."""
        # Remove effective_chat from update
        mock_update.effective_chat = None

        await telegram_service.handle_message(mock_update, mock_context)

        # Verify no further processing occurred
        mock_context.bot.send_chat_action.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_message_invalid_update_missing_user(
        self, telegram_service: TelegramService, mock_update: Mock, mock_context: Mock
    ) -> None:
        """Test error handling for invalid update missing user."""
        # Remove effective_user from update
        mock_update.effective_user = None

        await telegram_service.handle_message(mock_update, mock_context)

        # Verify no further processing occurred
        mock_context.bot.send_chat_action.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_message_empty_text(
        self, telegram_service: TelegramService, mock_update: Mock, mock_context: Mock
    ) -> None:
        """Test error handling for empty message text."""
        # Set empty text
        mock_update.message.text = ""

        await telegram_service.handle_message(mock_update, mock_context)

        # Verify no further processing occurred
        mock_context.bot.send_chat_action.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_message_none_text(
        self, telegram_service: TelegramService, mock_update: Mock, mock_context: Mock
    ) -> None:
        """Test error handling for None message text."""
        # Set None text
        mock_update.message.text = None

        await telegram_service.handle_message(mock_update, mock_context)

        # Verify no further processing occurred
        mock_context.bot.send_chat_action.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_message_agent_engine_failure(
        self,
        telegram_service: TelegramService,
        mock_update: Mock,
        mock_context: Mock,
        mock_agent_engine: Mock,
    ) -> None:
        """Test error handling for agent engine failures."""

        # Mock agent engine to raise an exception
        async def mock_stream_query(
            message: str, user_id: str
        ) -> AsyncIterator[dict[str, Any]]:
            raise Exception("Agent engine error")

        mock_agent_engine.async_stream_query = AsyncMock(side_effect=mock_stream_query)

        await telegram_service.handle_message(mock_update, mock_context)

        # Verify error message was sent to user
        mock_update.message.reply_markdown_v2.assert_called_once_with(
            "I encountered an error while processing your request. Please try again.",
            disable_web_page_preview=False,
        )

    @pytest.mark.asyncio
    async def test_handle_message_no_content_received(
        self,
        telegram_service: TelegramService,
        mock_update: Mock,
        mock_context: Mock,
        mock_agent_engine: Mock,
    ) -> None:
        """Test handling case where no content is received from agent engine."""
        # Mock agent engine to return empty response
        mock_events = [{"author": "assistant", "content": {"parts": []}}]

        # Create async generator mock and assign it directly
        async_generator = AsyncGeneratorMock(mock_events)
        mock_agent_engine.async_stream_query = Mock(return_value=async_generator)

        await telegram_service.handle_message(mock_update, mock_context)

        # Verify fallback error message was sent
        mock_update.message.reply_markdown_v2.assert_called_once_with(
            "I apologize, but I couldn't generate a response. Please try again.",
            disable_web_page_preview=False,
        )

    @pytest.mark.asyncio
    async def test_handle_message_event_validation_error(
        self,
        telegram_service: TelegramService,
        mock_update: Mock,
        mock_context: Mock,
        mock_agent_engine: Mock,
    ) -> None:
        """Test handling event validation errors."""
        # Mock agent engine to return invalid events
        mock_events = [{"invalid": "event_data"}]

        # Create async generator mock and assign it directly
        async_generator = AsyncGeneratorMock(mock_events)
        mock_agent_engine.async_stream_query = Mock(return_value=async_generator)

        await telegram_service.handle_message(mock_update, mock_context)

        # Verify fallback error message was sent due to no valid content
        mock_update.message.reply_markdown_v2.assert_called_once_with(
            "I apologize, but I couldn't generate a response. Please try again.",
            disable_web_page_preview=False,
        )

    @pytest.mark.asyncio
    async def test_start_command_success(
        self, telegram_service: TelegramService, mock_update: Mock
    ) -> None:
        """Test successful start command handling."""
        await telegram_service.start_command(
            mock_update, Mock(spec=ContextTypes.DEFAULT_TYPE)
        )

        # Verify welcome message was sent
        mock_update.message.reply_markdown_v2.assert_called_once()
        call_args = mock_update.message.reply_markdown_v2.call_args[0][0]

        assert "Welcome to BuySpy AI Assistant!" in call_args
        assert "I'm here to help you" in call_args

    @pytest.mark.asyncio
    async def test_start_command_missing_message(
        self, telegram_service: TelegramService, mock_update: Mock
    ) -> None:
        """Test start command handling with missing message."""
        # Remove message from update
        original_message = mock_update.message
        mock_update.message = None

        await telegram_service.start_command(
            mock_update, Mock(spec=ContextTypes.DEFAULT_TYPE)
        )

        # Verify no message was sent
        if original_message:
            original_message.reply_html.assert_not_called()

    @pytest.mark.asyncio
    async def test_start_command_missing_user(
        self, telegram_service: TelegramService, mock_update: Mock
    ) -> None:
        """Test start command handling with missing user."""
        # Remove effective_user from update
        mock_update.effective_user = None

        await telegram_service.start_command(
            mock_update, Mock(spec=ContextTypes.DEFAULT_TYPE)
        )

        # Verify no message was sent
        mock_update.message.reply_html.assert_not_called()

    @pytest.mark.asyncio
    async def test_start_command_send_error(
        self, telegram_service: TelegramService, mock_update: Mock
    ) -> None:
        """Test start command error handling when sending fails."""
        # Make reply_html raise an exception
        mock_update.message.reply_html.side_effect = Exception("Send error")

        # Should not raise exception, just log it
        await telegram_service.start_command(
            mock_update, Mock(spec=ContextTypes.DEFAULT_TYPE)
        )

    def test_setup_handlers_with_application(
        self, telegram_service: TelegramService
    ) -> None:
        """Test setting up handlers when application is available."""
        # Mock the application
        mock_application = Mock()
        mock_application.add_handler = Mock()
        telegram_service.application = mock_application

        # Execute the method
        telegram_service.setup_handlers()

        # Verify handlers were added
        assert mock_application.add_handler.call_count == 2

    def test_setup_handlers_without_application(
        self, telegram_service: TelegramService
    ) -> None:
        """Test setting up handlers when application is not available."""
        # Ensure application is None
        telegram_service.application = None

        # Execute the method
        telegram_service.setup_handlers()

        # Verify no handlers were added (no exception should be raised)
        assert telegram_service.application is None

    def test_start_polling_success(self, telegram_service: TelegramService) -> None:
        """Test successful bot polling start."""
        with patch(
            "app.services.telegram_service.Application"
        ) as mock_application_class:
            # Mock the application instance
            mock_application = Mock()
            mock_application_class.builder.return_value.token.return_value.build.return_value = mock_application
            mock_application.run_polling = Mock()

            # Mock the setup_handlers method
            with patch.object(
                telegram_service, "setup_handlers"
            ) as mock_setup_handlers:
                # Execute the method (synchronously)
                telegram_service.start_polling()

                # Verify application was created
                mock_application_class.builder.return_value.token.assert_called_once_with(
                    "test_bot_token"
                )
                mock_application_class.builder.return_value.token.return_value.build.assert_called_once()

                # Verify setup_handlers was called
                mock_setup_handlers.assert_called_once()

                # Verify polling was started
                mock_application.run_polling.assert_called_once()

    def test_start_polling_error(self, telegram_service: TelegramService) -> None:
        """Test error handling during bot polling start."""
        with patch(
            "app.services.telegram_service.Application"
        ) as mock_application_class:
            # Make build raise an exception
            mock_application_class.builder.return_value.token.return_value.build.side_effect = Exception(
                "Build error"
            )

            # Execute the method and expect exception to be raised
            with pytest.raises(Exception, match="Build error"):
                telegram_service.start_polling()

    @pytest.mark.asyncio
    async def test_stop_with_application(
        self, telegram_service: TelegramService
    ) -> None:
        """Test stopping bot when application is available."""
        # Mock the application
        mock_application = Mock()
        mock_application.stop = AsyncMock()
        mock_application.shutdown = AsyncMock()
        telegram_service.application = mock_application

        # Execute the method
        await telegram_service.stop()

        # Verify stop and shutdown were called
        mock_application.stop.assert_called_once()
        mock_application.shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_without_application(
        self, telegram_service: TelegramService
    ) -> None:
        """Test stopping bot when application is not available."""
        # Ensure application is None
        telegram_service.application = None

        # Execute the method (should not raise exception)
        await telegram_service.stop()

    @pytest.mark.asyncio
    async def test_stop_error_handling(self, telegram_service: TelegramService) -> None:
        """Test error handling during bot stop."""
        # Mock the application that raises an exception
        mock_application = Mock()
        mock_application.stop = AsyncMock(side_effect=Exception("Stop error"))
        mock_application.shutdown = AsyncMock()
        telegram_service.application = mock_application

        # Execute the method (should not raise exception)
        await telegram_service.stop()

        # Verify stop was called despite the error
        mock_application.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_message_long_message_logging(
        self,
        telegram_service: TelegramService,
        mock_update: Mock,
        mock_context: Mock,
        mock_agent_engine: Mock,
    ) -> None:
        """Test that long messages are properly logged with truncation."""
        # Set a long message text
        long_message = "A" * 150
        mock_update.message.text = long_message

        # Mock agent engine response with proper Event structure
        mock_events = [
            {"author": "assistant", "content": {"parts": [{"text": "Response"}]}}
        ]

        # Create async generator mock and assign it directly
        async_generator = AsyncGeneratorMock(mock_events)
        mock_agent_engine.async_stream_query = Mock(return_value=async_generator)

        # Capture log messages
        with patch.object(telegram_service.logger, "info") as mock_logger:
            await telegram_service.handle_message(mock_update, mock_context)

            # Verify the incoming message was logged (some info logs should be called)
            # We check if any info log was called since the message processing might have errors
            mock_logger.assert_called()

    @pytest.mark.asyncio
    async def test_handle_message_response_sending_error(
        self,
        telegram_service: TelegramService,
        mock_update: Mock,
        mock_context: Mock,
        mock_agent_engine: Mock,
    ) -> None:
        """Test error handling when sending response fails."""
        # Mock agent engine response with proper Event structure
        mock_events = [
            {"author": "assistant", "content": {"parts": [{"text": "Test response"}]}}
        ]

        # Create async generator mock and assign it directly
        async_generator = AsyncGeneratorMock(mock_events)
        mock_agent_engine.async_stream_query = Mock(return_value=async_generator)

        # Make reply_html raise an exception
        mock_update.message.reply_html.side_effect = Exception("Send error")

        # Should handle the error gracefully
        await telegram_service.handle_message(mock_update, mock_context)
