import os
from pathlib import Path

from dotenv import load_dotenv

from file_storage import GoogleCloudStorage
from user_settings import UserSettings
from multi_user_document_storage import MultiUserDocumentStorageManager
from tg import TelegramBot

if __name__ == "__main__":
    load_dotenv()
    
    # Initialize file storage
    file_storage = GoogleCloudStorage(Path(os.environ["GOOGLE_APPLICATION_CREDENTIALS"]), "yid-tg2notion")
    
    # Initialize user settings manager
    user_settings = UserSettings()
    
    # Initialize multi-user document storage manager
    storage_manager = MultiUserDocumentStorageManager(
        notion_token=os.environ["NOTION_TOKEN"],
        file_storage=file_storage,
        user_settings=user_settings
    )
    
    # Initialize and run bot
    bot = TelegramBot(
        token=os.getenv("TELEGRAM_TOKEN"),
        storage_manager=storage_manager
    )
    bot.run_polling()
