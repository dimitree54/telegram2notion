import os
from pathlib import Path

from dotenv import load_dotenv

from document_storage import RecognisingDocumentsStorage, NotionDocumentsStorage
from file_storage import GoogleCloudStorage
from recognisers import WebPageRecogniser, RedirectingFileRecogniser, PDFPlumberFileRecogniser, \
    SoundOnlyVideoRecogniser, VisionGPTImageRecogniser, WhisperAudioRecogniser
from tg import TelegramBot

if __name__ == "__main__":
    load_dotenv()
    file_storage = GoogleCloudStorage(Path(os.environ["GOOGLE_APPLICATION_CREDENTIALS"]), "tg2notion")
    base_document_storage = NotionDocumentsStorage(
        token=os.environ["NOTION_TOKEN"],
        parent_document_id=os.environ["NOTION_PARENT_DOCUMENT"],
        file_storage=file_storage,
    )
    audio_recogniser = WhisperAudioRecogniser()
    image_recogniser = VisionGPTImageRecogniser()
    video_recogniser = SoundOnlyVideoRecogniser(audio_recogniser)
    pdf_recogniser = PDFPlumberFileRecogniser(image_recogniser)
    file_recogniser = RedirectingFileRecogniser(
        audio_recogniser, image_recogniser, video_recogniser, pdf_recogniser
    )
    url_recogniser = WebPageRecogniser()
    document_storage = RecognisingDocumentsStorage(
        base_doc_storage=base_document_storage,
        audio_recogniser=audio_recogniser,
        image_recogniser=image_recogniser,
        video_recogniser=video_recogniser,
        handwriting_recogniser=image_recogniser,
        file_recogniser=file_recogniser,
        url_recogniser=url_recogniser,
    )
    bot = TelegramBot(
        token=os.getenv("TELEGRAM_TOKEN"),
        user_id=int(os.getenv("TELEGRAM_USER_ID")),
        doc_storage=document_storage
    )
    bot.run_polling()
