import os
import unittest
from pathlib import Path
from dotenv import load_dotenv

from document_storage import NotionDocumentsStorage
from file_storage import GoogleCloudStorage


class TestNotionDocumentStorage(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        load_dotenv()
        file_storage = GoogleCloudStorage(Path(__file__).parents[1] / "google_drive_creds.json", "tg2notion")
        self.doc_storage = NotionDocumentsStorage(os.environ["NOTION_TOKEN"], os.environ["NOTION_PARENT_DOCUMENT"], file_storage=file_storage)

    async def test_audio(self):
        await self.doc_storage.save_audio(audio_path=Path(__file__).parent / 'data' / "test.mp3", name="test_audio")

    async def test_image(self):
        await self.doc_storage.save_image(image_path=Path(__file__).parent / 'data' / "test.webp", name="test_image")

    async def test_video(self):
        await self.doc_storage.save_video(video_path=Path(__file__).parent / 'data' / "test.mp4", name="test_video")

    async def test_pdf(self):
        await self.doc_storage.save_file(file_path=Path(__file__).parent / 'data' / "test.pdf", name="test_pdf")
