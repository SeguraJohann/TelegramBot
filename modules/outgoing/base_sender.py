from abc import ABC, abstractmethod
from typing import Dict, List
from modules.base import BasePlugin


class BaseSender(BasePlugin, ABC):
    """
    Base class for OUTGOING plugins.
    These plugins only send messages on a schedule.
    """
    
    def __init__(self, telegram_client, scheduler):
        """Initialize the sender plugin."""
        super().__init__()  # Initialize BasePlugin
        self.client = telegram_client
        self.scheduler = scheduler
    
    @abstractmethod
    def get_schedule(self) -> Dict:
        """
        Return the schedule configuration for this plugin.
        
        Returns:
            Dict with trigger configuration (e.g., {'trigger': 'interval', 'minutes': 5})
        """
        pass
    
    @abstractmethod
    async def send(self):
        """
        Logic to send the message.
        This method is called by the scheduler.
        """
        pass
    
    @abstractmethod
    def get_recipients(self) -> List[int]:
        """
        Return list of chat_ids that should receive messages.
        
        Returns:
            List of chat IDs
        """
        pass
    
    def _get_plugin_type(self) -> str:
        """Return the type of plugin."""
        return "outgoing"
    
    def register_job(self):
        """Register this plugin's job with the scheduler using JobStorage."""
        try:
            if not self.validate_config():
                self.logger.error(f"Invalid configuration for {self.__class__.__name__}")
                return False
            
            # Create job data for persistence
            job_data = self.scheduler.job_storage.create_job_data(
                job_id=self.get_job_id(),
                plugin_type=self._get_plugin_type(),
                plugin_name=self.get_plugin_name(),
                plugin_class=self.__class__.__name__,
                schedule=self.get_schedule(),
                description=self.get_description(),
                active=True
            )
            
            # Register with scheduler manager
            success = self.scheduler.register_plugin_job(self, job_data)
            
            if success:
                self.logger.info(f"Registered and persisted job for {self.__class__.__name__}")
                return True
            else:
                self.logger.error(f"Failed to register job for {self.__class__.__name__}")
                return False
                
        except Exception as e:
            self.handle_error(e, "registering job")
            return False
    
    @abstractmethod
    def get_plugin_name(self) -> str:
        """
        Return the plugin directory name.
        
        Returns:
            str: Plugin directory name (e.g., 'tests', 'laundry')
        """
        pass
    
    def get_description(self) -> str:
        """
        Return a human-readable description of the plugin.
        Override in subclasses for custom descriptions.
        
        Returns:
            str: Plugin description
        """
        return f"{self.__class__.__name__} - OUTGOING plugin"
    
    async def _safe_send_wrapper(self):
        """Wrapper for send method with error handling and logging."""
        try:
            # Check if plugin is active before executing
            if not self._is_plugin_active():
                self.logger.debug(f"Plugin {self.__class__.__name__} is disabled, skipping execution")
                return

            await self.send()
            self.log_execution()
        except Exception as e:
            self.handle_error(e, "sending message")

    def _is_plugin_active(self) -> bool:
        """Check if plugin is currently active by reading from storage."""
        try:
            job_id = self.get_job_id()
            job_data = self.scheduler.job_storage.load_job(job_id)
            if job_data:
                return job_data.get('metadata', {}).get('active', True)
            return True  # Default to active if not found
        except Exception as e:
            self.logger.error(f"Error checking plugin status: {e}")
            return True  # Default to active on error
    
    def get_job_id(self) -> str:
        """Get the job ID for this plugin."""
        return f"{self.__class__.__name__}_job"