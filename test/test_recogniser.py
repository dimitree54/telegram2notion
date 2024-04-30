import unittest
from pathlib import Path
from dotenv import load_dotenv

from recognisers import WhisperAudioRecogniser, VisionGPTImageRecogniser, SoundOnlyVideoRecogniser, \
    PDFPlumberFileRecogniser, WebPageRecogniser


class TestFileRecognisers(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        load_dotenv()

    async def test_whisper_audio_recogniser(self):
        recogniser = WhisperAudioRecogniser()
        result = await recogniser.recognise(Path(__file__).parent / 'data' / "test.mp3")
        self.assertTrue(result.startswith("Раз") or result.startswith("1"))

    async def test_vision_gpt_image_recogniser(self):
        recogniser = VisionGPTImageRecogniser()
        result = await recogniser.recognise(Path(__file__).parent / 'data' / "test.webp")
        print(result)

    async def test_sound_only_video_recogniser(self):
        audio_recogniser = WhisperAudioRecogniser()
        recogniser = SoundOnlyVideoRecogniser(audio_recogniser)
        result = await recogniser.recognise(Path(__file__).parent / 'data' / "test.mp4")
        self.assertTrue(result.startswith("Раз") or result.startswith("1"))

    async def test_pdf_plumber_file_recogniser(self):
        image_recogniser = VisionGPTImageRecogniser()
        recogniser = PDFPlumberFileRecogniser(image_recogniser)
        result = await recogniser.recognise(Path(__file__).parent / 'data' / "test.pdf")
        print(result)


class TestURLRecogniser(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        load_dotenv()

    async def test_scrapy_url_recogniser(self):
        recogniser = WebPageRecogniser()
        result = await recogniser.recognise("https://github.com/dimitree54/tg_lila_bot")
        print(result)
