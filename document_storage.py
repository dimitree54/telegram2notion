from abc import ABC
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from notion_client import Client

from file_storage import FileStorage


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


class NotionDocumentsStorageBase(DocumentsStorage, ABC):
    """Base class for Notion document storage with common functionality."""
    
    def __init__(self, token: str, file_storage: FileStorage):
        self.file_storage = file_storage
        self.notion_client = Client(auth=token)

    def _build_header(self, name: str) -> Dict:
        """Build header for page creation. Must be implemented by subclasses."""
        raise NotImplementedError()

    @staticmethod
    def _build_text_block(text: str) -> List[Dict]:
        """
        Build text blocks for long text, splitting into multiple paragraphs if needed.
        Notion has a 2000 character limit per paragraph.
        """
        if not text:
            return []
        
        max_length = 2000
        blocks = []
        
        # Split text into chunks of max_length, trying to break at word boundaries
        while len(text) > max_length:
            # Find the last space within the limit
            split_pos = text.rfind(' ', 0, max_length)
            
            # If no space found, force split at max_length
            if split_pos == -1:
                split_pos = max_length
            
            chunk = text[:split_pos].strip()
            if chunk:
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": chunk}}]
                    }
                })
            
            text = text[split_pos:].strip()
        
        # Add the remaining text
        if text:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"text": {"content": text}}]
                }
            })
        
        return blocks

    def _create_page(self, name: str, children: List[Dict]):
        self.notion_client.pages.create(**self._build_header(name), children=children)

    async def save_text(self, name: str, text: str):
        self._create_page(name, self._build_text_block(text))

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
            children.extend(self._build_text_block(description))
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
            children.extend(self._build_text_block(description))
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
            children.extend(self._build_text_block(description))
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
            children.extend(self._build_text_block(description))
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
            children.extend(self._build_text_block(description))
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
            children.extend(self._build_text_block(description))
        self._create_page(name, children)


class NotionPageDocumentsStorage(NotionDocumentsStorageBase):
    """Notion storage that creates child pages under a parent page."""
    
    def __init__(self, token: str, parent_page_id: str, file_storage: FileStorage):
        super().__init__(token, file_storage)
        self.parent_page_id = parent_page_id

    def _build_header(self, name: str) -> Dict:
        return {
            "parent": {"page_id": self.parent_page_id},
            "properties": {"title": {"title": [{"text": {"content": name}}]}}
        }


class NotionDatabaseDocumentsStorage(NotionDocumentsStorageBase):
    """Notion storage that creates pages in a database."""
    
    def __init__(self, token: str, database_id: str, file_storage: FileStorage):
        super().__init__(token, file_storage)
        self.database_id = database_id

    def _build_header(self, name: str) -> Dict:
        return {
            "parent": {"database_id": self.database_id},
            "properties": {
                "Name": {
                    "title": [{"text": {"content": name}}]
                }
            }
        }
