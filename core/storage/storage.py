import json
import os
from typing import Dict, List, Optional, Any


class PluginStorage:
    """
    Storage manager for plugin data using JSON files.
    Provides CRUD operations for plugin persistence.
    """
    
    def __init__(self, plugin_data_dir: str):
        """Initialize storage for a specific plugin."""
        self.plugin_data_dir = plugin_data_dir
    
    def save(self, job_id: str, data: Dict[str, Any]) -> bool:
        """Save data to JSON file."""
        pass
    
    def load(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Load data from specific JSON file."""
        pass
    
    def load_all(self) -> List[Dict[str, Any]]:
        """Load all JSON files from plugin data directory."""
        pass
    
    def delete(self, job_id: str) -> bool:
        """Delete specific JSON file."""
        pass
    
    def exists(self, job_id: str) -> bool:
        """Check if specific JSON file exists."""
        pass
    
    def _ensure_data_directory(self):
        """Create data directory if it doesn't exist."""
        pass
    
    def _get_file_path(self, job_id: str) -> str:
        """Get full file path for a job_id."""
        pass