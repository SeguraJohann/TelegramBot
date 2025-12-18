import asyncio
import os
import sys
from dotenv import load_dotenv
from typing import Dict, Any, Optional

from core import SchedulerManager, TelegramClient
from modules.outgoing.tests.test_plugin import TestPlugin
from modules.incoming.plugin_manager.plugin_manager import PluginManagerCommand


def log(message):
    """Print to stderr with flush for immediate output."""
    print(message, flush=True, file=sys.stderr)


def plugin_loader(job_data: Dict[str, Any], telegram_client, scheduler) -> Optional[object]:
    """
    Plugin loader function for recreating plugin instances from job data.

    Args:
        job_data: Job configuration data
        telegram_client: TelegramClient instance
        scheduler: SchedulerManager instance

    Returns:
        Plugin instance or None if failed
    """
    try:
        plugin_type = job_data['plugin_type']
        plugin_name = job_data['plugin_name']
        plugin_class = job_data['plugin_class']

        log(f"Loading plugin: {plugin_type}/{plugin_name}/{plugin_class}")

        # Load OUTGOING plugins
        if plugin_type == 'outgoing':
            if plugin_name == 'tests' and plugin_class == 'TestPlugin':
                from modules.outgoing.tests.test_plugin import TestPlugin
                return TestPlugin(telegram_client, scheduler)

        # Load INCOMING plugins
        elif plugin_type == 'incoming':
            if plugin_name == 'plugin_manager' and plugin_class == 'PluginManagerCommand':
                from modules.incoming.plugin_manager.plugin_manager import PluginManagerCommand
                return PluginManagerCommand(telegram_client, scheduler)

        # Load HYBRID plugins (future)
        elif plugin_type == 'hybrid':
            log(f"HYBRID plugin loading not yet implemented for {plugin_name}")
            return None

        log(f"Unknown plugin: {plugin_type}/{plugin_name}/{plugin_class}")
        return None

    except Exception as e:
        log(f"Error loading plugin: {e}")
        import traceback
        log(traceback.format_exc())
        return None


async def main():
    """Main function with persistence system and polling."""

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

    print("Starting Telegram Bot with persistence and polling...")

    # Initialize core components
    scheduler = SchedulerManager()
    telegram_client = TelegramClient(token)

    # Initialize telegram client
    telegram_client.initialize()

    # Load all persisted plugins from storage
    log("Loading persisted plugins from storage...")
    all_jobs = scheduler.job_storage.load_all_jobs()

    loaded_outgoing = 0
    loaded_incoming = 0
    skipped_inactive = 0

    for job_data in all_jobs:
        job_id = job_data['job_id']
        plugin_type = job_data['plugin_type']
        is_active = job_data.get('metadata', {}).get('active', True)

        if not is_active:
            log(f"Skipping inactive plugin: {job_id}")
            skipped_inactive += 1
            continue

        try:
            # Create plugin instance
            plugin_instance = plugin_loader(job_data, telegram_client, scheduler)

            if not plugin_instance:
                log(f"Failed to load plugin: {job_id}")
                continue

            # Register based on type
            if plugin_type == 'outgoing':
                # For outgoing, register with scheduler
                schedule = job_data['schedule']
                success = scheduler.add_job(
                    func=plugin_instance._safe_send_wrapper,
                    job_id=job_id,
                    **schedule
                )
                if success:
                    scheduler._plugin_registry[job_id] = plugin_instance
                    loaded_outgoing += 1
                    log(f"Loaded OUTGOING plugin: {job_id}")
                else:
                    log(f"Failed to register OUTGOING plugin: {job_id}")

            elif plugin_type == 'incoming':
                # For incoming, register handler (don't save to storage again)
                if plugin_instance.register_handler(save_to_storage=False):
                    loaded_incoming += 1
                    log(f"Loaded INCOMING plugin: {job_id}")
                else:
                    log(f"Failed to register INCOMING plugin: {job_id}")

            elif plugin_type == 'hybrid':
                # For hybrid, register both
                if plugin_instance.register():
                    loaded_outgoing += 1
                    loaded_incoming += 1
                    log(f"Loaded HYBRID plugin: {job_id}")
                else:
                    log(f"Failed to register HYBRID plugin: {job_id}")

        except Exception as e:
            log(f"Error loading plugin {job_id}: {e}")

    log(f"\nPlugin loading summary:")
    log(f"  - OUTGOING plugins loaded: {loaded_outgoing}")
    log(f"  - INCOMING plugins loaded: {loaded_incoming}")
    log(f"  - Inactive plugins skipped: {skipped_inactive}")

    # Initialize default plugins if nothing was loaded (first run)
    if loaded_outgoing == 0 and loaded_incoming == 0:
        log("\nNo plugins found. Initializing default plugins...")

        # Create test plugin
        log("Creating TestPlugin...")
        test_plugin = TestPlugin(telegram_client, scheduler)
        if test_plugin.register_job():
            log("TestPlugin registered successfully")

        # Create plugin manager
        log("Creating PluginManagerCommand...")
        plugin_manager = PluginManagerCommand(telegram_client, scheduler)
        if plugin_manager.register_handler():
            log("PluginManagerCommand registered successfully")

    # Start scheduler
    log("Starting scheduler...")
    scheduler.start()
    log("Scheduler started")

    log("\nBot started successfully!")
    log("\nActive scheduled jobs:")
    for job in scheduler.get_jobs():
        log(f"  - {job.id}: next run at {job.next_run_time}")

    log("\nRegistered commands:")
    log("  - /plugins - Manage bot plugins")

    log("\nPersisted jobs:")
    for job_data in scheduler.list_persisted_jobs():
        active_status = "ACTIVE" if job_data['metadata'].get('active', True) else "DISABLED"
        log(f"  - {job_data['job_id']}: {job_data['metadata']['description']} [{active_status}]")

    log("\nStarting polling for incoming messages...")
    log("Press Ctrl+C to stop the bot\n")

    try:
        # Start the Application polling
        # This will block and handle incoming messages
        application = telegram_client.get_application()
        await application.initialize()
        await application.start()
        await application.updater.start_polling()

        # Keep running until interrupted
        try:
            # Wait indefinitely
            await asyncio.Event().wait()
        except (KeyboardInterrupt, SystemExit):
            print("\nReceived stop signal...")

    except KeyboardInterrupt:
        print("\nStopping bot...")
    finally:
        # Cleanup
        print("Shutting down...")

        # Stop polling
        try:
            application = telegram_client.get_application()
            if application.updater.running:
                await application.updater.stop()
            if application.running:
                await application.stop()
            await application.shutdown()
        except Exception as e:
            print(f"Error stopping application: {e}")

        # Stop scheduler
        scheduler.shutdown()
        print("Bot stopped successfully!")


if __name__ == "__main__":
    asyncio.run(main())