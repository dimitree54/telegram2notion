import unittest
from pathlib import Path
from dotenv import load_dotenv

from recognisers import WhisperAudioRecogniser, VisionGPTImageRecogniser, SoundOnlyVideoRecogniser, \
    PDFPlumberFileRecogniser


class TestFileRecognisers(unittest.TestCase):
    def setUp(self):
        load_dotenv()

    def test_whisper_audio_recogniser(self):
        recogniser = WhisperAudioRecogniser()
        result = recogniser.recognise(Path(__file__).parent / 'data' / "test.mp3")
        self.assertTrue(result.startswith("Раз") or result.startswith("1"))

    def test_vision_gpt_image_recogniser(self):
        recogniser = VisionGPTImageRecogniser()
        result = recogniser.recognise(Path(__file__).parent / 'data' / "test.webp")
        print(result)

    def test_sound_only_video_recogniser(self):
        audio_recogniser = WhisperAudioRecogniser()
        recogniser = SoundOnlyVideoRecogniser(audio_recogniser)
        result = recogniser.recognise(Path(__file__).parent / 'data' / "test.mp4")
        self.assertTrue(result.startswith("Раз") or result.startswith("1"))

    def test_pdf_plumber_file_recogniser(self):
        image_recogniser = VisionGPTImageRecogniser()
        recogniser = PDFPlumberFileRecogniser(image_recogniser)
        result = recogniser.recognise(Path(__file__).parent / 'data' / "test.pdf")
        print(result)
