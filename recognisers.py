import asyncio
import base64
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path

import pdfplumber
import pandas as pd
from moviepy.editor import VideoFileClip
from openai import AsyncOpenAI

import scrapy
from scrapy.crawler import CrawlerProcess
from bs4 import BeautifulSoup


class FileRecogniser(ABC):
    @abstractmethod
    async def recognise(self, file_path: Path) -> str:
        pass


class WhisperAudioRecogniser(FileRecogniser):
    def __init__(self):
        self.client = AsyncOpenAI()

    async def recognise(self, file_path: Path) -> str:
        """Supported formats .mp3, .mp4, .mpeg, .mpga, .m4a, .wav, .webm"""
        with open(file_path, "rb") as audio_file:
            response = await self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
            return response


class VisionGPTImageRecogniser(FileRecogniser):
    def __init__(self):
        self.client = AsyncOpenAI()

    async def recognise(self, file_path: Path) -> str:
        """Supported formats .png .jpeg and .jpg, .webp, .gif"""
        with open(file_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        response = await self.client.chat.completions.create(
            model="gpt-4-vision-preview",
            temperature=0.0,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that describes images. Describe it very detailed, including every small detail. If there is text on image, transcribe it fully."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    ]
                }
            ],
            max_tokens=3000
        )
        description = response.choices[0].message.content
        return description


class SoundOnlyVideoRecogniser(FileRecogniser):
    def __init__(self, audio_recogniser: FileRecogniser):
        self.audio_recogniser = audio_recogniser

    async def recognise(self, file_path: Path) -> str:
        """Supported video formats include MP4, AVI, and MKV."""
        temp_audio_path = file_path.with_suffix('.mp3')

        def extract_audio():
            with VideoFileClip(str(file_path)) as video:
                video.audio.write_audiofile(str(temp_audio_path))

        await asyncio.get_running_loop().run_in_executor(None, extract_audio)
        result = await self.audio_recogniser.recognise(temp_audio_path)
        temp_audio_path.unlink()

        return result


class PDFPlumberFileRecogniser(FileRecogniser):
    def __init__(self, image_recogniser: FileRecogniser):
        self.image_recogniser = image_recogniser

    async def recognise(self, file_path: Path) -> str:
        all_text = 'PDF document: ' + file_path.name + '\n'
        with pdfplumber.open(file_path) as pdf:
            for page_index, page in enumerate(pdf.pages):
                if page_index != 0:
                    all_text += "\n\n"
                all_text += "Page: " + str(page_index) + "\n"
                page_text = page.extract_text()
                page_tables = page.extract_tables()
                page_images = page.images
                if page_text:
                    all_text += page_text + '\n'
                if len(page_tables) > 0:
                    all_text += f'\n\nTables on page {page_index}:\n'
                for table_index, table in enumerate(page_tables):
                    df = pd.DataFrame(table[1:], columns=table[0])
                    all_text += f"\n{table_index + 1}: {df.to_string(index=False)}\n"

                if len(page_images) > 0:
                    all_text += f'\n\nImages on page {page_index}:\n'
                for image_index, image in enumerate(page_images):
                    with tempfile.NamedTemporaryFile(delete=True, suffix='.png') as tmp:
                        image_path = Path(tmp.name)
                        page.to_image().original.crop((image["x0"], image["top"], image["x1"], image["bottom"])).save(
                            image_path, format="PNG")
                        recognized_text = await self.image_recogniser.recognise(image_path)
                    all_text += f"{image_index + 1}: {recognized_text}\n"

        return all_text


class RedirectingFileRecogniser(FileRecogniser):
    def __init__(self, audio_recogniser: FileRecogniser, image_recogniser: FileRecogniser, video_recogniser: FileRecogniser, pdf_recogniser: FileRecogniser):
        self.recognisers = self.create_recogniser_map(audio_recogniser, image_recogniser, video_recogniser, pdf_recogniser)

    @staticmethod
    def create_recogniser_map(audio_recogniser, image_recogniser, video_recogniser, pdf_recogniser):
        return {
            **dict.fromkeys(['.mp3', '.mpeg', '.mpga', '.m4a', '.wav', '.webm'], audio_recogniser),
            **dict.fromkeys(['.mp4', '.avi', '.mkv'], video_recogniser),
            **dict.fromkeys(['.jpeg', '.jpg', '.png', '.webp', '.gif'], image_recogniser),
            **dict.fromkeys(['.pdf'], pdf_recogniser),
        }

    def recognise(self, file_path: Path) -> str:
        ext = file_path.suffix.lower()
        if ext in self.recognisers:
            return self.recognisers[ext].recognise(file_path)
        else:
            raise ValueError(f'Unrecognised file extension {ext}')


class URLRecogniser(ABC):
    @abstractmethod
    async def recognise(self, url: str) -> str:
        pass


class WebPageRecogniser(URLRecogniser):
    async def recognise(self, url: str) -> str:
        process = CrawlerProcess({'USER_AGENT': 'Mozilla/5.0'})
        results = []

        class ContentSpider(scrapy.Spider):
            name = "content_spider"

            def start_requests(self):
                yield scrapy.Request(url=url, callback=self.parse)

            def parse(self, response):
                soup = BeautifulSoup(response.body, 'html.parser')
                for script in soup(["script", "style"]):  # Remove script and style elements
                    script.extract()
                text = soup.get_text(separator='\n', strip=True)
                results.append(text)

        process.crawl(ContentSpider)
        process.start()  # Blocks here until crawling is finished
        return '\n'.join(results)
