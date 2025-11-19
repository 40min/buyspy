import logging

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


class TelegramService:
    """Service for handling Telegram bot message routing to the agent engine."""

    def __init__(self, bot_token: str, agent_engine: AgentEngineApp):
        """Initialize the Telegram service with bot token and agent engine instance."""
        self.agent_engine = agent_engine
        self.bot_token = bot_token
        self.logger = logging.getLogger(__name__)
        self.application: Application | None = None

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

            # Log the incoming message
            self.logger.info(
                f"Received message from user {update.effective_user.id} in chat {chat_id}: {user_message[:100]}{'...' if len(user_message) > 100 else ''}"
            )

            # Send "typing" action to show the bot is processing
            await context.bot.send_chat_action(chat_id=chat_id, action="typing")

            # Initialize response text
            response_text = ""
            event_count = 0

            # Pass the message to the agent engine and process streaming response
            async for event in self.agent_engine.async_stream_query(
                message=user_message, user_id=str(update.effective_user.id)
            ):
                try:
                    # Validate the event
                    validated_event = Event.model_validate(event)
                    content = validated_event.content

                    # Extract text content from the event
                    if content and content.parts:
                        for part in content.parts:
                            if hasattr(part, "text") and part.text:
                                response_text += part.text
                                event_count += 1
                except Exception as event_error:
                    self.logger.warning(
                        f"Error processing event {event}: {event_error}"
                    )
                    continue

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

            # Send the response back to the user
            await update.message.reply_text(response_text)

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
                    await update.message.reply_text(error_message)
            except Exception as send_error:
                chat_id_str: str = (
                    str(update.effective_chat.id)
                    if update.effective_chat
                    else "unknown"
                )
                self.logger.error(
                    f"Failed to send error message to chat {chat_id_str}: {send_error}"
                )

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

    def stop(self) -> None:
        """Stop the bot gracefully."""
        try:
            if self.application:
                self.logger.info("Stopping Telegram bot...")
                self.application.stop()
                self.logger.info("Telegram bot stopped successfully")
        except Exception as e:
            self.logger.error(f"Error stopping Telegram bot: {e}", exc_info=True)
