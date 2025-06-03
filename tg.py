import tempfile
from datetime import datetime
from pathlib import Path

from pydub import AudioSegment
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackContext, filters, CommandHandler
from telegram.error import Conflict, NetworkError, RetryAfter
import logging
import asyncio

from multi_user_document_storage import MultiUserDocumentStorageManager

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def ogg_to_mp3(ogg_path, mp3_path):
    audio = AudioSegment.from_ogg(ogg_path)
    audio.export(mp3_path, format="mp3")


class TelegramBot:
    def __init__(self, token: str, storage_manager: MultiUserDocumentStorageManager):
        self.application = ApplicationBuilder().token(token=token).build()
        
        # Add error handler
        self.application.add_error_handler(self.error_handler)
        
        self.application.add_handler(CommandHandler("start", self.start_handler))
        self.application.add_handler(CommandHandler("status", self.status_handler))
        self.application.add_handler(CommandHandler("unregister", self.unregister_handler))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.text_handler))
        self.application.add_handler(MessageHandler(filters.ATTACHMENT, self.file_handler))
        self.storage_manager = storage_manager
        self._awaiting_database_id = set()  # Track users who are expected to send database ID

    async def error_handler(self, update: Update, context: CallbackContext) -> None:
        """Handle errors during bot operation."""
        logger.error(f"Exception while handling an update: {context.error}")
        
        # Handle specific error types
        if isinstance(context.error, Conflict):
            logger.error("Bot conflict detected - another instance may be running")
            return
        elif isinstance(context.error, RetryAfter):
            logger.warning(f"Rate limited, retrying after {context.error.retry_after} seconds")
            await asyncio.sleep(context.error.retry_after)
            return
        elif isinstance(context.error, NetworkError):
            logger.warning("Network error occurred, will retry")
            return
        
        # For user-facing errors, try to send a message
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ An unexpected error occurred. Please try again later."
                )
            except Exception as e:
                logger.error(f"Failed to send error message to user: {e}")

    def run_polling(self):
        print("Multi-user bot is running...")
        
        # Add retry logic for conflicts
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.application.run_polling(
                    drop_pending_updates=True,  # Drop pending updates to avoid conflicts
                    close_loop=False
                )
                break
            except Conflict as e:
                logger.error(f"Conflict error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    print(f"Retrying in 5 seconds... (attempt {attempt + 2}/{max_retries})")
                    import time
                    time.sleep(5)
                else:
                    print("❌ Failed to start bot after multiple attempts. Please check:")
                    print("1. No other bot instances are running")
                    print("2. No webhooks are configured for this bot")
                    print("3. The bot token is correct")
                    raise
            except Exception as e:
                logger.error(f"Unexpected error starting bot: {e}")
                raise

    async def start_handler(self, update: Update, context: CallbackContext) -> None:
        """Handle /start command."""
        user_id = update.message.from_user.id
        
        if self.storage_manager.is_user_registered(user_id):
            await update.message.reply_text(
                "✅ You are already registered!\n"
                "You can send me text messages, files, images, audio, or video and I'll save them to your Notion database.\n\n"
                "Commands:\n"
                "/status - Check your registration status\n"
                "/unregister - Remove your registration"
            )
        else:
            await update.message.reply_text(
                "👋 Welcome to the Telegram to Notion bot!\n\n"
                "To get started, please send me your Notion Database ID.\n"
                "You can find it in the URL of your Notion database page.\n\n"
                "Example: If your database URL is:\n"
                "https://www.notion.so/myworkspace/abc123def456...\n"
                "Then your Database ID is: abc123def456...\n\n"
                "Just paste the Database ID as a regular message."
            )
            self._awaiting_database_id.add(user_id)

    async def status_handler(self, update: Update, context: CallbackContext) -> None:
        """Handle /status command."""
        user_id = update.message.from_user.id
        
        if self.storage_manager.is_user_registered(user_id):
            database_id = self.storage_manager.user_settings.get_database_id(user_id)
            await update.message.reply_text(
                f"✅ You are registered!\n"
                f"Database ID: {database_id[:8]}...{database_id[-8:] if len(database_id) > 16 else database_id}\n\n"
                f"You can send me any content and I'll save it to your Notion database."
            )
        else:
            await update.message.reply_text(
                "❌ You are not registered yet.\n"
                "Send /start to begin the registration process."
            )

    async def unregister_handler(self, update: Update, context: CallbackContext) -> None:
        """Handle /unregister command."""
        user_id = update.message.from_user.id
        
        if self.storage_manager.unregister_user(user_id):
            await update.message.reply_text(
                "✅ You have been unregistered successfully.\n"
                "Send /start if you want to register again."
            )
        else:
            await update.message.reply_text(
                "❌ You were not registered.\n"
                "Send /start to register."
            )

    async def text_handler(self, update: Update, context: CallbackContext) -> None:
        try:
            user_id = update.message.from_user.id
            message_text = update.message.text
            
            # Check if user is awaiting database ID registration
            if user_id in self._awaiting_database_id:
                await self._handle_database_id_registration(update, message_text)
                return
            
            # Get user's document storage
            doc_storage = self.storage_manager.get_user_storage(user_id)
            if not doc_storage:
                await update.message.reply_text(
                    "❌ You are not registered yet.\n"
                    "Send /start to register with your Notion Database ID."
                )
                return
            
            # Save text message
            name = f"text message from {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
            await doc_storage.save_text(name=name, text=message_text)
            await update.message.reply_text(f"✅ Document '{name}' saved to your Notion database")
            
        except Exception as e:
            # Shorten error message to avoid Telegram limit
            error_msg = str(e)[:500] + "..." if len(str(e)) > 500 else str(e)
            await update.message.reply_text(f"❌ Error: {error_msg}")

    async def _handle_database_id_registration(self, update: Update, database_id: str) -> None:
        """Handle database ID registration for a user."""
        user_id = update.message.from_user.id
        
        # Basic validation of database ID (should be alphanumeric with possible dashes)
        cleaned_id = database_id.strip().replace('-', '')
        if len(cleaned_id) < 20 or not all(c.isalnum() for c in cleaned_id):
            await update.message.reply_text(
                "❌ That doesn't look like a valid Notion Database ID.\n"
                "Please make sure you're sending the correct Database ID.\n\n"
                "It should be a long string of letters and numbers, like:\n"
                "abc123def456ghi789jkl012mno345pqr678"
            )
            return
        
        try:
            # Try to register the user
            self.storage_manager.register_user(user_id, database_id.strip())
            
            # Test the connection by trying to access the database
            # This is a simple validation - in real app you might want to do more thorough check
            
            self._awaiting_database_id.discard(user_id)
            await update.message.reply_text(
                "🎉 Registration successful!\n\n"
                "You can now send me:\n"
                "• Text messages\n"
                "• Images\n"
                "• Audio files\n"
                "• Video files\n"
                "• Documents\n\n"
                "I'll save everything to your Notion database.\n\n"
                "Commands:\n"
                "/status - Check registration status\n"
                "/unregister - Remove registration"
            )
            
        except Exception as e:
            error_msg = str(e)[:300] + "..." if len(str(e)) > 300 else str(e)
            await update.message.reply_text(
                f"❌ Failed to register with that Database ID.\n"
                f"Error: {error_msg}\n\n"
                "Please check:\n"
                "1. The Database ID is correct\n"
                "2. Your Notion integration has access to this database\n"
                "3. The database exists and is accessible\n\n"
                "Try sending the Database ID again."
            )

    async def file_handler(self, update: Update, context: CallbackContext) -> None:
        try:
            user_id = update.message.from_user.id
            
            # Get user's document storage
            doc_storage = self.storage_manager.get_user_storage(user_id)
            if not doc_storage:
                await update.message.reply_text(
                    "❌ You are not registered yet.\n"
                    "Send /start to register with your Notion Database ID."
                )
                return
            
            attachments = update.message.effective_attachment
            if isinstance(attachments, tuple):
                attachment = attachments[-1]
            else:
                attachment = attachments
            document = await context.bot.get_file(attachment.file_id)
            file_ext = Path(document.file_path).suffix
            with tempfile.NamedTemporaryFile(delete=True, suffix=file_ext) as file:
                await document.download_to_drive(file.name)
                description = update.message.caption if update.message.caption else None
                if file_ext in [".oga", ".ogg"]:
                    with tempfile.NamedTemporaryFile(delete=True, suffix=".mp3") as mp3_file:
                        ogg_to_mp3(file.name, mp3_file.name)
                        name = f"audio from {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
                        await doc_storage.save_audio(name=name, audio_path=Path(mp3_file.name), description=description)
                elif file_ext in [".mp3", ".wav"]:
                    name = f"audio from {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
                    await doc_storage.save_audio(name=name, audio_path=Path(file.name), description=description)
                elif file_ext in [".mp4", ".mov"]:
                    name = f"video from {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
                    await doc_storage.save_video(name=name, video_path=Path(file.name), description=description)
                elif file_ext in [".jpg", ".png", ".jpeg", ".gif", ".webp"]:
                    name = f"image from {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
                    await doc_storage.save_image(name=name, image_path=Path(file.name), description=description)
                else:
                    name = f"file from {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
                    await doc_storage.save_file(name=name, file_path=Path(file.name), description=description)
                await update.message.reply_text(f"✅ File '{name}' saved to your Notion database")
        except Exception as e:
            # Shorten error message to avoid Telegram limit
            error_msg = str(e)[:500] + "..." if len(str(e)) > 500 else str(e)
            await update.message.reply_text(f"❌ Error: {error_msg}")
