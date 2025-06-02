from typing import Dict, Optional
from document_storage import DocumentsStorage, NotionDatabaseDocumentsStorage
from file_storage import FileStorage
from user_settings import UserSettings


class MultiUserDocumentStorageManager:
    """Manages document storage instances for multiple users."""
    
    def __init__(self, notion_token: str, file_storage: FileStorage, user_settings: UserSettings):
        self.notion_token = notion_token
        self.file_storage = file_storage
        self.user_settings = user_settings
        self._storage_cache: Dict[int, DocumentsStorage] = {}
    
    def get_user_storage(self, user_id: int) -> Optional[DocumentsStorage]:
        """Get document storage for a specific user."""
        if not self.user_settings.is_user_registered(user_id):
            return None
        
        # Check if storage is already cached
        if user_id in self._storage_cache:
            return self._storage_cache[user_id]
        
        # Create new storage instance
        database_id = self.user_settings.get_database_id(user_id)
        if database_id:
            storage = NotionDatabaseDocumentsStorage(
                token=self.notion_token,
                database_id=database_id,
                file_storage=self.file_storage
            )
            self._storage_cache[user_id] = storage
            return storage
        
        return None
    
    def register_user(self, user_id: int, database_id: str) -> DocumentsStorage:
        """Register a new user with their database ID."""
        self.user_settings.set_database_id(user_id, database_id)
        
        # Clear cache for this user if exists
        if user_id in self._storage_cache:
            del self._storage_cache[user_id]
        
        # Create and cache new storage
        storage = NotionDatabaseDocumentsStorage(
            token=self.notion_token,
            database_id=database_id,
            file_storage=self.file_storage
        )
        self._storage_cache[user_id] = storage
        return storage
    
    def is_user_registered(self, user_id: int) -> bool:
        """Check if user is registered."""
        return self.user_settings.is_user_registered(user_id)
    
    def unregister_user(self, user_id: int) -> bool:
        """Unregister a user."""
        # Remove from cache
        if user_id in self._storage_cache:
            del self._storage_cache[user_id]
        
        # Remove from settings
        return self.user_settings.remove_user(user_id) 