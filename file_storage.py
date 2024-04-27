import asyncio
import io
import os
from abc import ABC, abstractmethod
from pathlib import Path

import aiofiles
from google.oauth2 import service_account
from googleapiclient.discovery import build, Resource  # noqa
from googleapiclient.http import MediaIoBaseUpload


class FileStorage(ABC):
    @abstractmethod
    async def save_and_get_url(self, file_path: Path) -> str:
        pass


class GoogleDriveStorage(FileStorage):
    def __init__(self, service_account_file_path: Path):
        scopes = ['https://www.googleapis.com/auth/drive.file']
        creds = service_account.Credentials.from_service_account_file(
            str(service_account_file_path), scopes=scopes)
        self.service = build('drive', 'v3', credentials=creds)

    async def save_and_get_url(self, file_path: Path) -> str:
        async with aiofiles.open(file_path, 'rb') as file_data:
            bytes_data = await file_data.read()
        file_metadata = {'name': os.path.basename(file_path)}

        def create_file():
            media = MediaIoBaseUpload(io.BytesIO(bytes_data), mimetype='application/octet-stream')
            return self.service.files().create(
                body=file_metadata, media_body=media, fields='id').execute()

        def create_permission(file_id_):
            permission = {'type': 'anyone', 'role': 'reader'}
            self.service.permissions().create(
                fileId=file_id, body=permission).execute()
            return file_id_

        loop = asyncio.get_running_loop()
        file = await loop.run_in_executor(None, create_file)
        file_id = file.get('id')
        await loop.run_in_executor(None, create_permission, file_id)

        return f"https://drive.google.com/uc?id={file_id}"
