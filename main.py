import asyncio
import os
from dotenv import load_dotenv
from typing import Dict, Any, Optional

from core import SchedulerManager, TelegramClient
from modules.outgoing.tests.test_plugin import TestPlugin


def plugin_loader(job_data: Dict[str, Any]) -> Optional[object]:
    """
    Plugin loader function for recreating plugin instances from job data.
    
    Args:
        job_data: Job configuration data
        
    Returns:
        Plugin instance or None if failed
    """
    try:
        plugin_type = job_data['plugin_type']
        plugin_name = job_data['plugin_name']
        plugin_class = job_data['plugin_class']
        
        print(f"Loading plugin: {plugin_type}/{plugin_name}/{plugin_class}")
        
        # For now, hardcode test plugin loading
        # In future, implement dynamic plugin discovery
        if plugin_type == 'outgoing' and plugin_name == 'tests' and plugin_class == 'TestPlugin':
            # Get telegram client and scheduler from global scope
            # This is a simplified approach for testing
            return None  # Will implement proper plugin loading later
        
        print(f"Unknown plugin: {plugin_type}/{plugin_name}/{plugin_class}")
        return None
        
    except Exception as e:
        print(f"Error loading plugin: {e}")
        return None


async def main():
    """Main function with new persistence system."""
    
    # Load environment variables
    load_dotenv()
    
    # Get configuration
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    admin_chat_id = os.getenv('ADMIN_CHAT_ID')
    
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN not found in .env file")
        return
    
    if not admin_chat_id:
        print("Error: ADMIN_CHAT_ID not found in .env file")
        return
    
    print("Starting Telegram Bot with new persistence system...")
    
    # Initialize core components
    scheduler = SchedulerManager()
    telegram_client = TelegramClient(token)
    
    # Initialize telegram client
    telegram_client.initialize()
    
    # Load persisted jobs (empty on first run)
    loaded_jobs = scheduler.load_persisted_jobs(plugin_loader)
    print(f"Loaded {loaded_jobs} persisted jobs from storage")
    
    # Initialize and register test plugin (for first-time setup)
    if loaded_jobs == 0:
        print("No persisted jobs found. Creating test plugin...")
        test_plugin = TestPlugin(telegram_client, scheduler)
        
        if test_plugin.register_job():
            print("Test plugin registered and persisted successfully")
        else:
            print("Failed to register test plugin")
            return
    
    # Start scheduler
    scheduler.start()
    
    print("Bot started successfully!")
    print("Active jobs:")
    for job in scheduler.get_jobs():
        print(f"  - {job.id}: next run at {job.next_run_time}")
    
    print("\nPersisted jobs:")
    for job_data in scheduler.list_persisted_jobs():
        print(f"  - {job_data['job_id']}: {job_data['metadata']['description']}")
    
    print("\nTest plugin will send messages every 5 minutes")
    print("Press Ctrl+C to stop the bot")
    
    try:
        # Keep the bot running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping bot...")
        scheduler.shutdown()
        print("Bot stopped successfully!")


if __name__ == "__main__":
    asyncio.run(main())