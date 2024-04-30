from abc import ABC
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from notion_client import Client

from file_storage import FileStorage
from recognisers import FileRecogniser, URLRecogniser


class DocumentsStorage(ABC):
    async def save_text(self, name: str, text: str):
        raise NotImplementedError()

    async def save_image(self, name: str, image_path: Path, description: Optional[str] = None):
        raise NotImplementedError()

    async def save_audio(self, name: str, audio_path: Path, description: Optional[str] = None):
        raise NotImplementedError()

    async def save_video(self, name: str, video_path: Path, description: Optional[str] = None):
        raise NotImplementedError()

    async def save_handwriting(self, name: str, image_path: Path, description: Optional[str] = None):
        raise NotImplementedError()

    async def save_link(self, name: str, url: str, description: Optional[str] = None):
        raise NotImplementedError()

    async def save_file(self, name: str, file_path: Path, description: Optional[str] = None):
        raise NotImplementedError()

    async def save_reminder(self, name: str, content: str, due_date: datetime):
        raise NotImplementedError()

    async def save_todo(self, name: str, task: str, category: str):
        raise NotImplementedError()


class NotionDocumentsStorage(DocumentsStorage):
    def __init__(self, token: str, parent_document_id: str, file_storage: FileStorage):
        self.file_storage = file_storage
        self.parent_document_id = parent_document_id
        self.notion_client = Client(auth=token)

    def _build_header(self, name: str) -> Dict:
        return {
            "parent": {"page_id": self.parent_document_id},
            "properties": {"title": {"title": [{"text": {"content": name}}]}}
        }

    @staticmethod
    def _build_text_block(text: str) -> Dict:
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"text": {"content": text}}]
            }
        }

    def _create_page(self, name: str, children: List[Dict]):
        self.notion_client.pages.create(**self._build_header(name), children=children)

    async def save_text(self, name: str, text: str):
        self._create_page(name, [self._build_text_block(text)])

    async def save_image(self, name: str, image_path: Path, description: Optional[str] = None):
        image_url = await self.file_storage.save_and_get_url(image_path)
        image_block = {
            "object": "block",
            "type": "image",
            "image": {
                "type": "external",
                "external": {
                    "url": image_url
                }
            }
        }
        children = [image_block]
        if description:
            children.append(self._build_text_block(description))
        self._create_page(name, children)

    async def save_audio(self, name: str, audio_path: Path, description: Optional[str] = None):
        audio_url = await self.file_storage.save_and_get_url(audio_path)
        audio_block = {
            "object": "block",
            "type": "audio",
            "audio": {
                "type": "external",
                "external": {
                    "url": audio_url
                }
            }
        }
        children = [audio_block]
        if description:
            children.append(self._build_text_block(description))
        self._create_page(name, children)

    async def save_video(self, name: str, video_path: Path, description: Optional[str] = None):
        video_url = await self.file_storage.save_and_get_url(video_path)
        video_block = {
            "object": "block",
            "type": "video",
            "video": {
                "type": "external",
                "external": {
                    "url": video_url
                }
            }
        }
        children = [video_block]
        if description:
            children.append(self._build_text_block(description))
        self._create_page(name, children)

    async def save_handwriting(self, name: str, image_path: Path, description: Optional[str] = None):
        image_url = await self.file_storage.save_and_get_url(image_path)
        image_block = {
            "object": "block",
            "type": "image",
            "image": {
                "type": "external",
                "external": {
                    "url": image_url
                }
            }
        }
        children = [image_block]
        if description:
            children.append(self._build_text_block(description))
        self._create_page(name, children)

    async def save_link(self, name: str, url: str, description: Optional[str] = None):
        link_block = {
            "object": "block",
            "type": "bookmark",
            "bookmark": {
                "url": url
            }
        }
        children = [link_block]
        if description:
            children.append(self._build_text_block(description))
        self._create_page(name, children)

    async def save_file(self, name: str, file_path: Path, description: Optional[str] = None):
        file_url = await self.file_storage.save_and_get_url(file_path)
        file_block = {
            "object": "block",
            "type": "file",
            "file": {
                "type": "external",
                "external": {
                    "url": file_url
                }
            }
        }
        children = [file_block]
        if description:
            children.append(self._build_text_block(description))
        self._create_page(name, children)


class RecognisingDocumentsStorage(DocumentsStorage):
    def __init__(
            self,
            base_doc_storage: DocumentsStorage,
            audio_recogniser: FileRecogniser,
            image_recogniser: FileRecogniser,
            video_recogniser: FileRecogniser,
            handwriting_recogniser: FileRecogniser,
            file_recogniser: FileRecogniser,
            url_recogniser: URLRecogniser,
    ):
        self.video_recogniser = video_recogniser
        self.image_recogniser = image_recogniser
        self.handwriting_recogniser = handwriting_recogniser
        self.file_recogniser = file_recogniser
        self.url_recogniser = url_recogniser
        self.audio_recogniser = audio_recogniser
        self.base_doc_storage = base_doc_storage

    async def save_text(self, name: str, text: str):
        await self.base_doc_storage.save_text(name, text)

    async def save_image(self, name: str, image_path: Path, description: Optional[str] = None):
        recognised_description = await self.image_recogniser.recognise(image_path)
        if description:
            recognised_description += '\n\n' + description
        await self.base_doc_storage.save_image(name, image_path, recognised_description)

    async def save_audio(self, name: str, audio_path: Path, description: Optional[str] = None):
        recognised_description = await self.audio_recogniser.recognise(audio_path)
        if description:
            recognised_description += '\n\n' + description
        await self.base_doc_storage.save_audio(name, audio_path, recognised_description)

    async def save_video(self, name: str, video_path: Path, description: Optional[str] = None):
        recognised_description = await self.video_recogniser.recognise(video_path)
        if description:
            recognised_description += '\n\n' + description
        await self.base_doc_storage.save_video(name, video_path, recognised_description)

    async def save_handwriting(self, name: str, image_path: Path, description: Optional[str] = None):
        recognised_description = await self.handwriting_recogniser.recognise(image_path)
        if description:
            recognised_description += '\n\n' + description
        await self.base_doc_storage.save_handwriting(name, image_path, recognised_description)

    async def save_link(self, name: str, url: str, description: Optional[str] = None):
        recognised_description = await self.url_recogniser.recognise(url)
        if description:
            recognised_description += '\n\n' + description
        await self.base_doc_storage.save_link(name, url, recognised_description)

    async def save_file(self, name: str, file_path: Path, description: Optional[str] = None):
        recognised_description = await self.file_recogniser.recognise(file_path)
        if description:
            recognised_description += '\n\n' + description
        await self.base_doc_storage.save_file(name, file_path, recognised_description)
