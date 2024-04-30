import tempfile
import traceback
from datetime import datetime
from pathlib import Path

from pydub import AudioSegment
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackContext, filters

from document_storage import DocumentsStorage


def ogg_to_mp3(ogg_path, mp3_path):
    audio = AudioSegment.from_ogg(ogg_path)
    audio.export(mp3_path, format="mp3")


class TelegramBot:
    def __init__(self, token: str, user_id: int,doc_storage: DocumentsStorage):
        self.application = ApplicationBuilder().token(token=token).build()
        self.application.add_handler(MessageHandler(filters.TEXT, self.text_handler))
        self.application.add_handler(MessageHandler(filters.ATTACHMENT, self.file_handler))
        self.doc_storage = doc_storage
        self.user_id = user_id

    def run_polling(self):
        print("Bot is running...")
        self.application.run_polling()

    async def text_handler(self, update: Update, context: CallbackContext) -> None:  # noqa
        try:
            if update.message.from_user.id != self.user_id:
                return
            name = f"text message from {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
            await self.doc_storage.save_text(name=name, text=update.message.text)
            await update.message.reply_text(f"Document {name} saved")
        except Exception as e:
            # send error text and stacktrace to user
            await update.message.reply_text(f"Error: {e}\n\n{traceback.format_exc()}")

    async def file_handler(self, update: Update, context: CallbackContext) -> None:
        try:
            if update.message.from_user.id != self.user_id:
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
                    with tempfile.NamedTemporaryFile(delete=True, suffix=file_ext) as mp3_file:
                        ogg_to_mp3(file.name, mp3_file.name)
                        name = f"audio from {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
                        await self.doc_storage.save_audio(name=name, audio_path=Path(file.name), description=description)
                elif file_ext in [".mp3", ".wav"]:
                    name = f"audio from {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
                    await self.doc_storage.save_audio(name=name, audio_path=Path(file.name), description=description)
                elif file_ext in [".mp4", ".mov"]:
                    name = f"video from {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
                    await self.doc_storage.save_video(name=name, video_path=Path(file.name), description=description)
                elif file_ext in [".jpg", ".png", ".jpeg", ".gif", ".webp"]:
                    name = f"image from {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
                    await self.doc_storage.save_image(name=name, image_path=Path(file.name), description=description)
                else:
                    name = f"file from {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
                    await self.doc_storage.save_file(name=name, file_path=Path(file.name), description=description)
                await update.message.reply_text(f"File {name} saved")
        except Exception as e:
            # send error text and stacktrace to user
            await update.message.reply_text(f"Error: {e}\n\n{traceback.format_exc()}")
