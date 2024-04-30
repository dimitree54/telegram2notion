import os
import uuid
from abc import ABC, abstractmethod
from mimetypes import guess_type
from pathlib import Path

import aiofiles
from google.cloud import storage
from google.oauth2 import service_account


class FileStorage(ABC):
    @abstractmethod
    async def save_and_get_url(self, file_path: Path) -> str:
        pass


class GoogleCloudStorage(FileStorage):
    def __init__(self, service_account_file_path: Path, bucket_name: str):
        creds = service_account.Credentials.from_service_account_file(
            str(service_account_file_path))
        self.client = storage.Client(credentials=creds)
        self.bucket = self.client.bucket(bucket_name)

    async def save_and_get_url(self, file_path: Path) -> str:
        blob_name = str(uuid.uuid4()) + os.path.splitext(file_path.name)[1]
        blob = self.bucket.blob(blob_name)

        async with aiofiles.open(file_path, 'rb') as file_data:
            bytes_data = await file_data.read()

        mime_type = guess_type(file_path)[0] or 'application/octet-stream'
        blob.upload_from_string(bytes_data, content_type=mime_type)
        blob.make_public()
        return blob.public_url
