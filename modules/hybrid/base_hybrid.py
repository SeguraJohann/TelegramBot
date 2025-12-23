from abc import ABC, abstractmethod
from typing import Dict, List
from telegram import Update
from telegram.ext import ContextTypes
from modules.base import BasePlugin


class BaseHybrid(BasePlugin, ABC):
    """
    Base class for HYBRID plugins.
    These plugins combine OUTGOING (scheduled) and INCOMING (handler) functionality.

    Example use case: A reminder system where users can set reminders via commands,
    and the bot sends scheduled reminders.
    """

    def __init__(self, telegram_client, scheduler):
        """Initialize the hybrid plugin."""
        super().__init__()  # Initialize BasePlugin
        self.client = telegram_client
        self.scheduler = scheduler

    # OUTGOING methods (from BaseSender)

    @abstractmethod
    def get_schedule(self) -> Dict:
        """
        Return the schedule configuration for the outgoing functionality.

        Returns:
            Dict with trigger configuration (e.g., {'trigger': 'interval', 'minutes': 5})
        """
        pass

    @abstractmethod
    async def send(self):
        """
        Logic to send scheduled messages.
        This method is called by the scheduler.
        """
        pass

    @abstractmethod
    def get_recipients(self) -> List[int]:
        """
        Return list of chat_ids that should receive scheduled messages.

        Returns:
            List of chat IDs
        """
        pass

    # INCOMING methods (from BaseHandler)

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

    # Common methods

    def _get_plugin_type(self) -> str:
        """Return the type of plugin."""
        return "hybrid"

    @abstractmethod
    def get_plugin_name(self) -> str:
        """
        Return the plugin directory name.

        Returns:
            str: Plugin directory name (e.g., 'reminders', 'notifications')
        """
        pass

    def get_description(self) -> str:
        """
        Return a human-readable description of the plugin.
        Override in subclasses for custom descriptions.

        Returns:
            str: Plugin description
        """
        return f"{self.__class__.__name__} - HYBRID plugin"

    def get_job_id(self) -> str:
        """Get the job ID for this plugin."""
        return f"{self.__class__.__name__}_job"

    # Wrappers for error handling

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
            self.handle_error(e, "sending scheduled message")

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
            self.handle_error(e, "handling incoming message")
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

    # Registration methods

    def register_job(self) -> bool:
        """Register the scheduled job component of this hybrid plugin."""
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

    def register_handler(self, save_to_storage: bool = False) -> bool:
        """Register the handler component of this hybrid plugin."""
        try:
            from telegram.ext import CommandHandler, MessageHandler, filters

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

            self.logger.info(f"Handler component for {self.__class__.__name__} registered successfully")
            return True

        except Exception as e:
            self.handle_error(e, "registering handler")
            return False

    def register(self) -> bool:
        """
        Register both job and handler components of this hybrid plugin.

        Returns:
            bool: True if both components registered successfully
        """
        job_success = self.register_job()
        handler_success = self.register_handler()

        if job_success and handler_success:
            self.logger.info(f"Hybrid plugin {self.__class__.__name__} fully registered")
            return True
        else:
            self.logger.error(
                f"Hybrid plugin registration incomplete - "
                f"Job: {'OK' if job_success else 'FAILED'}, "
                f"Handler: {'OK' if handler_success else 'FAILED'}"
            )
            return False
