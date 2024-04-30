import unittest
from pathlib import Path

from dotenv import load_dotenv

from file_storage import GoogleCloudStorage


class TestFileStorage(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        load_dotenv()
        self.file_storage = GoogleCloudStorage(Path(__file__).parents[1] / "google_drive_creds.json", "tg2notion")

    async def test_audio(self):
        url = await self.file_storage.save_and_get_url(file_path=Path(__file__).parent / 'data' / "test.mp3")
        print("audio url:", url)

    async def test_image(self):
        url = await self.file_storage.save_and_get_url(file_path=Path(__file__).parent / 'data' / "test.webp")
        print("image url:", url)

    async def test_video(self):
        url = await self.file_storage.save_and_get_url(file_path=Path(__file__).parent / 'data' / "test.mp4")
        print("video url:", url)

    async def test_file(self):
        url = await self.file_storage.save_and_get_url(file_path=Path(__file__).parent / 'data' / "test.pdf")
        print("file url:", url)
