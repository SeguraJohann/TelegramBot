from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from modules.base import BasePlugin


class BaseHandler(BasePlugin, ABC):
    """
    Base class for INCOMING plugins.
    These plugins respond to messages, commands, and other user interactions.
    """

    def __init__(self, telegram_client, scheduler):
        """Initialize the handler plugin."""
        super().__init__()  # Initialize BasePlugin
        self.client = telegram_client
        self.scheduler = scheduler

    @abstractmethod
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Logic to handle incoming messages/commands.
        This method is called when a matching message is received.

        Args:
            update: Telegram update object
            context: Telegram context object
        """
        pass

    @abstractmethod
    def get_handler_type(self) -> str:
        """
        Return the type of handler.

        Returns:
            str: Handler type ('command', 'message', 'callback', etc.)
        """
        pass

    @abstractmethod
    def get_handler_config(self) -> Dict:
        """
        Return handler configuration.

        For command handlers:
            {'command': 'start', 'description': 'Start the bot'}

        For message handlers:
            {'filters': filters.TEXT & ~filters.COMMAND}

        Returns:
            Dict with handler configuration
        """
        pass

    def _get_plugin_type(self) -> str:
        """Return the type of plugin."""
        return "incoming"

    @abstractmethod
    def get_plugin_name(self) -> str:
        """
        Return the plugin directory name.

        Returns:
            str: Plugin directory name (e.g., 'plugin_manager', 'help')
        """
        pass

    def get_description(self) -> str:
        """
        Return a human-readable description of the plugin.
        Override in subclasses for custom descriptions.

        Returns:
            str: Plugin description
        """
        return f"{self.__class__.__name__} - INCOMING plugin"

    def get_job_id(self) -> str:
        """Get the job ID for this plugin."""
        return f"{self.__class__.__name__}_handler"

    async def _safe_handle_wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Wrapper for handle method with error handling and logging."""
        try:
            # Check if plugin is active before executing
            if not self._is_plugin_active():
                self.logger.debug(f"Plugin {self.__class__.__name__} is disabled, skipping execution")
                return

            await self.handle(update, context)
            self.log_execution()
        except Exception as e:
            self.handle_error(e, "handling message")
            # Optionally notify user of error
            if update.effective_chat:
                try:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="An error occurred while processing your request."
                    )
                except:
                    pass

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

    def register_handler(self, save_to_storage: bool = True) -> bool:
        """
        Register this plugin's handler with the Telegram application.

        Args:
            save_to_storage: Whether to save to storage (False when loading from storage)

        Returns:
            bool: True if registered successfully
        """
        try:
            if not self.validate_config():
                self.logger.error(f"Invalid configuration for {self.__class__.__name__}")
                return False

            handler_type = self.get_handler_type()
            handler_config = self.get_handler_config()
            application = self.client.get_application()

            if not application:
                self.logger.error("Telegram application not initialized")
                return False

            # Create appropriate handler based on type
            if handler_type == 'command':
                command = handler_config.get('command')
                if not command:
                    self.logger.error("Command name not specified in handler_config")
                    return False

                handler = CommandHandler(command, self._safe_handle_wrapper)
                application.add_handler(handler)
                self.logger.info(f"Registered command handler: /{command}")

            elif handler_type == 'message':
                message_filters = handler_config.get('filters', filters.TEXT)
                handler = MessageHandler(message_filters, self._safe_handle_wrapper)
                application.add_handler(handler)
                self.logger.info(f"Registered message handler with filters")

            else:
                self.logger.error(f"Unsupported handler type: {handler_type}")
                return False

            # Save to storage only if this is a new registration
            if save_to_storage:
                # Create job data for persistence (incoming plugins don't have schedules)
                job_data = self.scheduler.job_storage.create_job_data(
                    job_id=self.get_job_id(),
                    plugin_type=self._get_plugin_type(),
                    plugin_name=self.get_plugin_name(),
                    plugin_class=self.__class__.__name__,
                    schedule={'trigger': 'none'},  # No schedule for incoming plugins
                    description=self.get_description(),
                    active=True
                )

                # Save to storage
                self.scheduler.job_storage.save_job(job_data)
                self.logger.info(f"Handler {self.__class__.__name__} saved to storage")

            # Register in plugin registry
            self.scheduler._plugin_registry[self.get_job_id()] = self

            self.logger.info(f"Handler {self.__class__.__name__} registered successfully")
            return True

        except Exception as e:
            self.handle_error(e, "registering handler")
            return False

    def unregister_handler(self) -> bool:
        """Unregister this plugin's handler from the Telegram application."""
        try:
            # Remove from storage
            self.scheduler.job_storage.delete_job(self.get_job_id())

            # Remove from plugin registry
            self.scheduler._plugin_registry.pop(self.get_job_id(), None)

            # Note: telegram.ext doesn't provide a clean way to remove specific handlers
            # They are removed when the application is restarted

            self.logger.info(f"Handler {self.__class__.__name__} unregistered")
            return True

        except Exception as e:
            self.handle_error(e, "unregistering handler")
            return False
