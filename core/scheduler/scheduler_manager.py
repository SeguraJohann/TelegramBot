import asyncio
from typing import Dict, List, Optional, Any, Callable
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.job import Job
from modules.storage import JobStorage


class SchedulerManager:
    """
    Manager for APScheduler with file-based job persistence.
    Handles job lifecycle, persistence, and restoration without database dependencies.
    """
    
    def __init__(self, storage_dir: str = "storage"):
        """Initialize the scheduler manager."""
        self.scheduler = AsyncIOScheduler()
        self.job_storage = JobStorage(storage_dir)
        self._plugin_registry = {}  # Maps job_id to plugin instances
    
    def add_job(self, func: Callable, trigger: str, job_id: str, **kwargs) -> bool:
        """Add a new job to the scheduler."""
        try:
            self.scheduler.add_job(
                func=func,
                trigger=trigger,
                id=job_id,
                **kwargs
            )
            print(f"Job {job_id} added successfully")
            return True
        except Exception as e:
            print(f"Error adding job {job_id}: {e}")
            return False
    
    def register_plugin_job(self, plugin_instance, job_data: Dict[str, Any]) -> bool:
        """
        Register a plugin job with scheduler and persistence.
        
        Args:
            plugin_instance: Instance of the plugin
            job_data: Job configuration data
            
        Returns:
            bool: True if registered successfully
        """
        try:
            job_id = job_data['job_id']
            schedule = job_data['schedule']
            
            # Register plugin instance
            self._plugin_registry[job_id] = plugin_instance
            
            # Add job to scheduler
            success = self.add_job(
                func=plugin_instance._safe_send_wrapper,
                job_id=job_id,
                **schedule
            )
            
            if success:
                # Save to persistent storage
                self.job_storage.save_job(job_data)
                print(f"Plugin job {job_id} registered and persisted")
                return True
            else:
                # Remove from registry if failed
                self._plugin_registry.pop(job_id, None)
                return False
                
        except Exception as e:
            print(f"Error registering plugin job {job_data.get('job_id', 'unknown')}: {e}")
            self._plugin_registry.pop(job_data.get('job_id'), None)
            return False
    
    def remove_job(self, job_id: str) -> bool:
        """Remove a job from the scheduler and storage."""
        try:
            # Remove from scheduler
            self.scheduler.remove_job(job_id)
            
            # Remove from storage
            self.job_storage.delete_job(job_id)
            
            # Remove from plugin registry
            self._plugin_registry.pop(job_id, None)
            
            print(f"Job {job_id} removed successfully")
            return True
        except Exception as e:
            print(f"Error removing job {job_id}: {e}")
            return False
    
    def reschedule_job(self, job_id: str, trigger: str, **kwargs) -> bool:
        """Reschedule an existing job."""
        try:
            self.scheduler.reschedule_job(job_id, trigger=trigger, **kwargs)
            print(f"Job {job_id} rescheduled successfully")
            return True
        except Exception as e:
            print(f"Error rescheduling job {job_id}: {e}")
            return False
    
    def get_jobs(self) -> List[Job]:
        """Get all jobs from the scheduler."""
        return self.scheduler.get_jobs()
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get a specific job by ID."""
        return self.scheduler.get_job(job_id)
    
    def start(self):
        """Start the scheduler."""
        try:
            if not self.scheduler.running:
                self.scheduler.start()
                print("Scheduler started successfully")
        except Exception as e:
            print(f"Error starting scheduler: {e}")
    
    def shutdown(self, wait: bool = True):
        """Shutdown the scheduler."""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown(wait=wait)
                print("Scheduler shutdown successfully")
        except Exception as e:
            print(f"Error shutting down scheduler: {e}")
    
    def load_persisted_jobs(self, plugin_loader_func: Callable) -> int:
        """
        Load persisted jobs from storage and recreate them in scheduler.
        
        Args:
            plugin_loader_func: Function that takes job_data and returns plugin instance
            
        Returns:
            int: Number of jobs successfully loaded
        """
        loaded_count = 0
        
        try:
            all_jobs = self.job_storage.load_all_jobs()
            
            for job_data in all_jobs:
                if not job_data.get('metadata', {}).get('active', True):
                    print(f"Skipping inactive job {job_data['job_id']}")
                    continue
                
                try:
                    # Use plugin loader to get instance
                    plugin_instance = plugin_loader_func(job_data)
                    
                    if plugin_instance:
                        # Register the plugin job
                        job_id = job_data['job_id']
                        schedule = job_data['schedule']
                        
                        # Register plugin instance
                        self._plugin_registry[job_id] = plugin_instance
                        
                        # Add job to scheduler
                        success = self.add_job(
                            func=plugin_instance._safe_send_wrapper,
                            job_id=job_id,
                            **schedule
                        )
                        
                        if success:
                            loaded_count += 1
                            print(f"Loaded persisted job: {job_id}")
                        else:
                            self._plugin_registry.pop(job_id, None)
                            print(f"Failed to load job: {job_id}")
                    else:
                        print(f"Failed to load plugin for job: {job_data['job_id']}")
                        
                except Exception as e:
                    print(f"Error loading job {job_data.get('job_id', 'unknown')}: {e}")
            
            print(f"Loaded {loaded_count} persisted jobs")
            return loaded_count
            
        except Exception as e:
            print(f"Error loading persisted jobs: {e}")
            return 0
    
    def list_persisted_jobs(self) -> List[Dict[str, Any]]:
        """List all persisted jobs from storage."""
        return self.job_storage.load_all_jobs()
    
    @property
    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self.scheduler.running