import io
import os
from abc import ABC, abstractmethod
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build, Resource  # noqa
from googleapiclient.http import MediaIoBaseUpload

from pydantic import BaseModel


class FileStorage(ABC):
    @abstractmethod
    def save_and_get_url(self, file_path: Path) -> str:
        pass


def authenticate_google_drive(service_account_file_path: Path) -> Resource:
    scopes = ['https://www.googleapis.com/auth/drive.file']
    creds = service_account.Credentials.from_service_account_file(
        str(service_account_file_path), scopes=scopes)
    return build('drive', 'v3', credentials=creds)


class GoogleDriveStorage(FileStorage, BaseModel):
    service: Resource

    class Config:
        arbitrary_types_allowed = True

    def save_and_get_url(self, file_path: Path) -> str:
        with open(file_path, 'rb') as file_data:
            bytes_data = file_data.read()
        file_metadata = {'name': os.path.basename(file_path)}
        media = MediaIoBaseUpload(io.BytesIO(bytes_data), mimetype='application/octet-stream')
        file = self.service.files().create(  # noqa
            body=file_metadata, media_body=media, fields='id').execute()
        file_id = file.get('id')
        permission = {
            'type': 'anyone',
            'role': 'reader',
        }
        self.service.permissions().create(  # noqa
            fileId=file_id, body=permission).execute()
        return f"https://drive.google.com/uc?id={file_id}"


def main():
    service_account_file_path = Path('google_drive_creds.json')
    service = authenticate_google_drive(service_account_file_path)
    storage = GoogleDriveStorage(service=service)
    file_path = Path('/Users/dmitryr/Downloads/test.webp')
    file_url = storage.save_and_get_url(file_path)
    print(f"File uploaded successfully! Access it here: {file_url}")


if __name__ == '__main__':
    main()
