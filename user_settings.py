import json
import os
from pathlib import Path
from typing import Dict, Optional, Set


class UserSettings:
    """Manages persistent user settings, specifically database IDs for each user."""
    
    def __init__(self, settings_file: Path = Path("user_settings.json")):
        self.settings_file = settings_file
        self._settings: Dict[str, Dict[str, str]] = {}
        self._load_settings()
    
    def _load_settings(self) -> None:
        """Load settings from file."""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    self._settings = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                print(f"Error loading settings: {e}. Starting with empty settings.")
                self._settings = {}
        else:
            self._settings = {}
    
    def _save_settings(self) -> None:
        """Save settings to file."""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self._settings, f, indent=2)
        except OSError as e:
            print(f"Error saving settings: {e}")
    
    def get_database_id(self, user_id: int) -> Optional[str]:
        """Get database ID for a user."""
        user_key = str(user_id)
        return self._settings.get(user_key, {}).get("database_id")
    
    def set_database_id(self, user_id: int, database_id: str) -> None:
        """Set database ID for a user."""
        user_key = str(user_id)
        if user_key not in self._settings:
            self._settings[user_key] = {}
        self._settings[user_key]["database_id"] = database_id
        self._save_settings()
    
    def is_user_registered(self, user_id: int) -> bool:
        """Check if user has database ID configured."""
        return self.get_database_id(user_id) is not None
    
    def get_registered_users(self) -> Set[int]:
        """Get set of all registered user IDs."""
        return {int(user_id) for user_id in self._settings.keys() 
                if self._settings[user_id].get("database_id")}
    
    def remove_user(self, user_id: int) -> bool:
        """Remove user settings. Returns True if user was removed, False if not found."""
        user_key = str(user_id)
        if user_key in self._settings:
            del self._settings[user_key]
            self._save_settings()
            return True
        return False 