import asyncio
import logging
from typing import Any
from venv import logger

from google.adk.events.event import Event
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.agent_engine_app import AgentEngineApp
from app.app_utils.telegram_markdown import (
    convert_urls_to_links,
    escape_markdown_v2,
)
from app.services.budget_service import BudgetService


class TelegramService:
    """Service for handling Telegram bot message routing to the agent engine."""

    def __init__(
        self,
        bot_token: str,
        agent_engine: AgentEngineApp,
        budget_service: BudgetService,
        timeout_seconds: int = 600,
    ):
        """Initialize the Telegram service with bot token and agent engine instance.

        Args:
            bot_token: Telegram bot token
            agent_engine: Agent engine instance
            budget_service: Budget service for rate limiting
            timeout_seconds: Timeout for agent processing in seconds (default: 600 = 10 minutes)
        """
        self.agent_engine = agent_engine
        self.bot_token = bot_token
        self.budget_service = budget_service
        self.timeout_seconds = timeout_seconds
        self.logger = logging.getLogger(__name__)
        self.application: Application | None = None
        self._sessions: set[str] = set()

    async def handle_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle incoming messages from Telegram users."""
        try:
            # Check for required attributes
            if (
                not update.message
                or not update.effective_chat
                or not update.effective_user
            ):
                self.logger.warning("Update missing required attributes")
                return

            # Extract user message and chat_id
            user_message = update.message.text
            if not user_message:
                self.logger.warning("Message has no text")
                return
            chat_id = update.effective_chat.id
            user_id = str(update.effective_user.id)

            # Check user budget before processing message
            if not await self.budget_service.check_and_increment(user_id):
                self.logger.warning(f"User {user_id} exceeded message budget")
                await update.message.reply_text(
                    "⚠️ You've reached your daily message limit. Please try again in 24 hours."
                )
                return

            # Log the incoming message
            self.logger.info(
                f"Received message from user {update.effective_user.id} in chat {chat_id}: {user_message[:100]}{'...' if len(user_message) > 100 else ''}"
            )

            # Send "typing" action to show the bot is processing
            await context.bot.send_chat_action(chat_id=chat_id, action="typing")

            session_id = await self._get_or_create_adk_session_id(
                telegram_user_id=str(update.effective_user.id),
                telegram_chat_id=str(chat_id),
            )

            logging.info(f"Using session ID: {session_id}")

            # Pass the message to the agent engine and process streaming response with timeout
            processing_task = None
            response_text = ""

            try:
                # Start the agent processing as a task
                processing_task = asyncio.create_task(
                    self._process_agent_response(
                        user_message,
                        user_id=str(update.effective_user.id),
                        session_id=str(chat_id),
                        context=context,
                        chat_id=str(chat_id),
                    )
                )

                # Wait for completion with timeout
                response_text, _event_count = await asyncio.wait_for(
                    processing_task, timeout=self.timeout_seconds
                )

            except asyncio.TimeoutError:
                # Cancel the processing task if it's still running
                if processing_task and not processing_task.done():
                    processing_task.cancel()

                self.logger.warning(
                    f"Agent processing timed out after {self.timeout_seconds} seconds for user {update.effective_user.id}"
                )
                response_text = (
                    "I apologize, but my processing is taking longer than expected. "
                    "Please try your request again, or simplify your question if possible."
                )
            except Exception as processing_error:
                self.logger.error(
                    f"Error during agent processing: {processing_error}", exc_info=True
                )
                response_text = "I encountered an error while processing your request. Please try again."

            # Handle case where no content was received
            if not response_text:
                response_text = (
                    "I apologize, but I couldn't generate a response. Please try again."
                )
                self.logger.warning(
                    f"No content received from agent engine for message: {user_message[:100]}"
                )

            self.logger.info(
                f"Sending response ({len(response_text)} chars) to chat {chat_id}"
            )

            self.logger.info(f"Raw output from agent text: {response_text}")

            # Convert raw URLs to Markdown links (if any exist)
            formatted_text = convert_urls_to_links(response_text)

            self.logger.info(f"After converting URLs to links: {formatted_text}")

            # Escape markdown while preserving link syntax
            formatted_text = escape_markdown_v2(formatted_text)

            self.logger.info(f"Sending formatted text: {formatted_text}")
            await update.message.reply_markdown_v2(
                formatted_text, disable_web_page_preview=False
            )

        except Exception as e:
            # Include comprehensive error handling
            user_id = update.effective_user.id if update.effective_user else "unknown"
            self.logger.error(
                f"Error handling message from user {user_id}: {e}",
                exc_info=True,
            )

            # Send user-friendly error message to Telegram
            error_message = "I apologize, but I encountered an error processing your message. Please try again in a moment."
            try:
                if update.message:
                    await update.message.reply_markdown_v2(
                        error_message, disable_web_page_preview=False
                    )
            except Exception as send_error:
                chat_id_str: str = (
                    str(update.effective_chat.id)
                    if update.effective_chat
                    else "unknown"
                )
                self.logger.error(
                    f"Failed to send error message to chat {chat_id_str}: {send_error}",
                    exc_info=True,
                )

    async def _get_or_create_adk_session_id(
        self, telegram_user_id: str, telegram_chat_id: str
    ) -> str:
        """
        Retrieves the existing ADK session ID for a chat, or creates a new one
        and stores it if one doesn't exist yet.
        """

        # Check local storage first
        if telegram_chat_id in self._sessions:
            logger.warning(f"Using existing session ID ({telegram_chat_id})")
            return telegram_chat_id

        try:
            # The 'user_id' parameter is for long-term memory association (Memory Bank feature)
            await self.agent_engine.async_create_session(
                user_id=telegram_user_id, session_id=telegram_chat_id
            )
            logger.warning(
                f"Created new session ID ({telegram_chat_id}) for chat {telegram_chat_id}"
            )
            self._sessions.add(telegram_chat_id)
        except Exception:
            logger.warning(f"Session in ADKalready exists for chat {telegram_chat_id}")
            self._sessions.add(telegram_chat_id)

        return telegram_chat_id

    async def _process_agent_response(
        self,
        user_message: str,
        user_id: str,
        session_id: str,
        context: Any,
        chat_id: str,
    ) -> tuple[str, int]:
        """Process agent response and return the accumulated text and event count.

        Args:
            user_message: The user message to process
            user_id: User identifier
            session_id: Session identifier

        Returns:
            Tuple of (response_text, event_count)
        """
        response_text = ""
        event_count = 0

        # Process streaming response from agent
        async for event in self.agent_engine.async_stream_query(
            message=user_message,
            user_id=user_id,
            session_id=session_id,
        ):
            try:
                # Validate the event
                validated_event = Event.model_validate(event)

                if validated_event.get_function_calls():
                    for call in validated_event.get_function_calls():
                        # Immediately send a status update to the user
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=f"⚙️ The agent is using a tool: `{call.name}`...",
                        )
                elif validated_event.content and validated_event.content.parts:
                    # This is the final LLM response text
                    for part in validated_event.content.parts:
                        if hasattr(part, "text") and part.text:
                            response_text += part.text
                            event_count += 1

            except Exception as event_error:
                self.logger.warning(f"Error processing event {event}: {event_error}")
                continue

        return response_text, event_count

    async def start_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle the /start command."""
        # Check for required attributes
        if not update.message or not update.effective_user:
            self.logger.warning("Update missing required attributes for start command")
            return

        welcome_message = (
            "👋 Welcome to BuySpy AI Assistant!\n\n"
            "I'm here to help you with information and answer your questions. "
            "Just send me a message and I'll do my best to assist you.\n\n"
            "You can ask me about:\n"
            "• Weather information\n"
            "• Current time\n"
            "• And much more!\n\n"
            "What can I help you with today?"
        )

        try:
            await update.message.reply_text(welcome_message)
            self.logger.info(f"Sent welcome message to user {update.effective_user.id}")
        except Exception as e:
            user_id = update.effective_user.id if update.effective_user else "unknown"
            self.logger.error(f"Failed to send welcome message to user {user_id}: {e}")

    def setup_handlers(self) -> None:
        """Set up message and command handlers."""
        if not self.application:
            return

        # Add handler for /start command
        start_handler = CommandHandler("start", self.start_command)
        self.application.add_handler(start_handler)

        # Add handler for text messages (excluding commands)
        message_handler = MessageHandler(
            filters.TEXT & ~filters.COMMAND, self.handle_message
        )
        self.application.add_handler(message_handler)

        self.logger.info("Telegram handlers set up successfully")

    def start_polling(self) -> None:
        """Start the bot polling loop."""
        try:
            # Initialize the application first
            self.application = Application.builder().token(self.bot_token).build()

            # Then set up handlers
            self.setup_handlers()

            self.logger.info("Starting Telegram bot polling...")

            self.logger.info(
                "Telegram bot is now running and listening for messages..."
            )

            # Start polling and run until stopped
            if self.application:
                self.application.run_polling()

        except Exception as e:
            self.logger.error(f"Error starting Telegram bot: {e}", exc_info=True)
            raise

    async def stop(self) -> None:
        """Stop the bot gracefully."""
        try:
            if self.application:
                self.logger.info("Stopping Telegram bot...")
                await self.application.stop()
                await self.application.shutdown()
                self.logger.info("Telegram bot stopped successfully")
        except Exception as e:
            self.logger.error(f"Error stopping Telegram bot: {e}", exc_info=True)
