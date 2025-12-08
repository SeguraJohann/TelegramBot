import os
from typing import Dict, List
from ..base_sender import BaseSender


class TestPlugin(BaseSender):
    """
    Test plugin for core functionality.
    Sends a test message every 5 minutes.
    """
    
    def get_schedule(self) -> Dict:
        """Send test message every 5 minutes."""
        return {
            'trigger': 'interval',
            'minutes': 5
        }
    
    def get_plugin_name(self) -> str:
        """Return the plugin directory name."""
        return "tests"
    
    def get_description(self) -> str:
        """Return plugin description."""
        return "Test plugin - sends message every 5 minutes to verify core functionality"
    
    async def send(self):
        """Send test message to all recipients."""
        message = "Test message - Bot core is working! (sent every 5 min)"
        
        for chat_id in self.get_recipients():
            success = await self.client.send_message(chat_id, message)
            if success:
                self.logger.info(f"Test message sent to {chat_id}")
            else:
                self.logger.error(f"Failed to send test message to {chat_id}")
    
    def get_recipients(self) -> List[int]:
        """Get recipients from environment variable."""
        admin_chat_id = os.getenv('ADMIN_CHAT_ID')
        
        if admin_chat_id:
            try:
                return [int(admin_chat_id)]
            except ValueError:
                self.logger.error(f"Invalid ADMIN_CHAT_ID: {admin_chat_id}")
                return []
        
        self.logger.warning("ADMIN_CHAT_ID not set")
        return []
    
    def validate_config(self) -> bool:
        """Validate plugin configuration."""
        recipients = self.get_recipients()
        if not recipients:
            self.logger.error("No valid recipients configured")
            return False
        return True