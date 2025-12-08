import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional


class JobStorage:
    """
    Storage manager for job persistence using JSON files.
    Handles saving, loading, and managing plugin job configurations.
    """
    
    def __init__(self, storage_dir: str = "storage"):
        """Initialize job storage."""
        self.storage_dir = storage_dir
        self._ensure_storage_directory()
    
    def _ensure_storage_directory(self):
        """Create storage directory if it doesn't exist."""
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)
    
    def _get_job_file_path(self, job_id: str) -> str:
        """Get the file path for a job's storage."""
        return os.path.join(self.storage_dir, f"{job_id}.json")
    
    def save_job(self, job_data: Dict[str, Any]) -> bool:
        """
        Save job data to JSON file.
        
        Args:
            job_data: Dictionary with job configuration
            
        Returns:
            bool: True if saved successfully
        """
        try:
            # Validate required fields
            if not self._validate_job_data(job_data):
                print(f"Invalid job data: {job_data}")
                return False
            
            # Add metadata
            job_data.update({
                'saved_at': datetime.now().isoformat(),
                'version': '1.0'
            })
            
            job_id = job_data['job_id']
            file_path = self._get_job_file_path(job_id)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(job_data, f, indent=2, ensure_ascii=False)
            
            print(f"Job {job_id} saved to storage")
            return True
            
        except Exception as e:
            print(f"Error saving job {job_data.get('job_id', 'unknown')}: {e}")
            return False
    
    def load_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Load job data from JSON file.
        
        Args:
            job_id: ID of the job to load
            
        Returns:
            Dict with job data or None if not found
        """
        file_path = self._get_job_file_path(job_id)
        
        if not os.path.exists(file_path):
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                job_data = json.load(f)
            
            if self._validate_job_data(job_data):
                return job_data
            else:
                print(f"Invalid job data in {job_id}")
                return None
                
        except Exception as e:
            print(f"Error loading job {job_id}: {e}")
            return None
    
    def load_all_jobs(self) -> List[Dict[str, Any]]:
        """
        Load all job files from storage directory.
        
        Returns:
            List of job data dictionaries
        """
        jobs = []
        
        if not os.path.exists(self.storage_dir):
            return jobs
        
        for filename in os.listdir(self.storage_dir):
            if not filename.endswith('.json'):
                continue
            
            job_id = filename[:-5]  # Remove .json extension
            job_data = self.load_job(job_id)
            
            if job_data:
                jobs.append(job_data)
            
        return jobs
    
    def delete_job(self, job_id: str) -> bool:
        """
        Delete job file from storage.
        
        Args:
            job_id: ID of the job to delete
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            file_path = self._get_job_file_path(job_id)
            
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Job {job_id} deleted from storage")
                return True
            else:
                print(f"Job {job_id} not found in storage")
                return False
                
        except Exception as e:
            print(f"Error deleting job {job_id}: {e}")
            return False
    
    def job_exists(self, job_id: str) -> bool:
        """
        Check if job file exists in storage.
        
        Args:
            job_id: ID of the job to check
            
        Returns:
            bool: True if job exists
        """
        file_path = self._get_job_file_path(job_id)
        return os.path.exists(file_path)
    
    def _validate_job_data(self, job_data: Dict[str, Any]) -> bool:
        """
        Validate job data structure.
        
        Args:
            job_data: Job data to validate
            
        Returns:
            bool: True if valid
        """
        required_fields = [
            'job_id',
            'plugin_type',
            'plugin_name', 
            'plugin_class',
            'schedule'
        ]
        
        # Check required fields
        for field in required_fields:
            if field not in job_data:
                print(f"Missing required field: {field}")
                return False
        
        # Validate plugin_type
        valid_types = ['outgoing', 'incoming', 'hybrid']
        if job_data['plugin_type'] not in valid_types:
            print(f"Invalid plugin_type: {job_data['plugin_type']}")
            return False
        
        # Validate schedule structure
        schedule = job_data['schedule']
        if not isinstance(schedule, dict) or 'trigger' not in schedule:
            print("Invalid schedule format")
            return False
        
        return True
    
    def create_job_data(
        self,
        job_id: str,
        plugin_type: str,
        plugin_name: str,
        plugin_class: str,
        schedule: Dict[str, Any],
        description: str = "",
        active: bool = True
    ) -> Dict[str, Any]:
        """
        Create standardized job data structure.
        
        Args:
            job_id: Unique identifier for the job
            plugin_type: Type of plugin (outgoing, incoming, hybrid)
            plugin_name: Name of the plugin directory
            plugin_class: Class name of the plugin
            schedule: Schedule configuration
            description: Human-readable description
            active: Whether the job is active
            
        Returns:
            Dict with standardized job data
        """
        return {
            'job_id': job_id,
            'plugin_type': plugin_type,
            'plugin_name': plugin_name,
            'plugin_class': plugin_class,
            'schedule': schedule,
            'metadata': {
                'description': description,
                'active': active,
                'created_at': datetime.now().isoformat(),
                'execution_count': 0,
                'last_execution': None,
                'error_count': 0
            }
        }