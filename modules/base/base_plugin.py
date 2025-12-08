import logging
import traceback
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional


class BasePlugin(ABC):
    """
    Base class for all plugins with common functionality.
    Provides error handling, logging, validation, and metadata management.
    """
    
    def __init__(self):
        """Initialize base plugin functionality."""
        self.logger = self._setup_logger()
        self.metadata = self._get_default_metadata()
        self._is_healthy = True
        self._last_error = None
        
    def _setup_logger(self) -> logging.Logger:
        """Setup standardized logger for the plugin."""
        logger_name = f"plugin.{self.__class__.__name__}"
        logger = logging.getLogger(logger_name)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
            
        return logger
    
    def _get_default_metadata(self) -> Dict[str, Any]:
        """Get default metadata for the plugin."""
        return {
            'plugin_name': self.__class__.__name__,
            'plugin_type': self._get_plugin_type(),
            'version': '1.0.0',
            'created_at': datetime.now().isoformat(),
            'last_execution': None,
            'execution_count': 0,
            'error_count': 0
        }
    
    @abstractmethod
    def _get_plugin_type(self) -> str:
        """Return the type of plugin (outgoing, incoming, hybrid)."""
        pass
    
    def handle_error(self, error: Exception, context: str = ""):
        """
        Standardized error handling for all plugins.
        
        Args:
            error: The exception that occurred
            context: Additional context about where the error occurred
        """
        self._is_healthy = False
        self._last_error = {
            'error': str(error),
            'type': error.__class__.__name__,
            'context': context,
            'timestamp': datetime.now().isoformat(),
            'traceback': traceback.format_exc()
        }
        
        self.metadata['error_count'] += 1
        
        error_msg = f"Error in {context}: {error}" if context else f"Error: {error}"
        self.logger.error(error_msg)
        self.logger.debug(f"Full traceback: {traceback.format_exc()}")
    
    def log_execution(self):
        """Log successful execution."""
        self.metadata['last_execution'] = datetime.now().isoformat()
        self.metadata['execution_count'] += 1
        self._is_healthy = True
        self.logger.info(f"Plugin {self.__class__.__name__} executed successfully")
    
    def validate_config(self) -> bool:
        """
        Validate plugin configuration.
        Override in subclasses for specific validation.
        
        Returns:
            bool: True if configuration is valid
        """
        try:
            # Basic validation - override in subclasses
            return True
        except Exception as e:
            self.handle_error(e, "configuration validation")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the plugin.
        
        Returns:
            Dict with health status and details
        """
        return {
            'healthy': self._is_healthy,
            'last_error': self._last_error,
            'metadata': self.metadata,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_plugin_info(self) -> Dict[str, Any]:
        """
        Get complete plugin information.
        
        Returns:
            Dict with plugin metadata and status
        """
        return {
            'name': self.__class__.__name__,
            'type': self._get_plugin_type(),
            'module': self.__module__,
            'healthy': self._is_healthy,
            'metadata': self.metadata
        }
    
    def graceful_shutdown(self):
        """
        Perform graceful shutdown cleanup.
        Override in subclasses for specific cleanup.
        """
        self.logger.info(f"Shutting down plugin {self.__class__.__name__}")
        # Override in subclasses for specific cleanup
    
    def safe_execute(self, func, *args, **kwargs):
        """
        Safely execute a function with error handling.
        
        Args:
            func: Function to execute
            *args, **kwargs: Arguments for the function
            
        Returns:
            Result of function or None if error occurred
        """
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            self.handle_error(e, f"executing {func.__name__}")
            return None
    
    async def safe_execute_async(self, func, *args, **kwargs):
        """
        Safely execute an async function with error handling.
        
        Args:
            func: Async function to execute
            *args, **kwargs: Arguments for the function
            
        Returns:
            Result of function or None if error occurred
        """
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            self.handle_error(e, f"executing async {func.__name__}")
            return None