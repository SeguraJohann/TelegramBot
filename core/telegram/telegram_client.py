from typing import Optional, Union
from telegram import Bot
from telegram.ext import Application


class TelegramClient:
    """
    Wrapper for python-telegram-bot API.
    Provides simplified interface for sending messages and files.
    """
    
    def __init__(self, token: str):
        """Initialize the telegram client."""
        self.token = token
        self.bot = None
        self.application = None
    
    async def send_message(self, chat_id: int, text: str, **kwargs) -> bool:
        """Send a text message."""
        try:
            if self.bot is None:
                raise Exception("Bot not initialized. Call initialize() first.")
            
            await self.bot.send_message(chat_id=chat_id, text=text, **kwargs)
            print(f"Message sent to {chat_id}: {text[:50]}...")
            return True
        except Exception as e:
            print(f"Error sending message to {chat_id}: {e}")
            return False
    
    async def send_photo(self, chat_id: int, photo: Union[str, bytes], caption: str = None, **kwargs) -> bool:
        """Send a photo."""
        pass
    
    async def send_document(self, chat_id: int, document: Union[str, bytes], filename: str = None, **kwargs) -> bool:
        """Send a document."""
        pass
    
    def initialize(self):
        """Initialize the bot and application."""
        self.application = Application.builder().token(self.token).build()
        self.bot = self.application.bot
        print("Telegram client initialized successfully")
    
    def get_application(self) -> Application:
        """Get the telegram application instance."""
        return self.application