import os
from typing import Dict
from telegram import Update
from telegram.ext import ContextTypes
from modules.incoming.base_handler import BaseHandler


class PluginManagerCommand(BaseHandler):
    """
    Plugin manager command handler.
    Allows administrators to manage plugins (enable/disable/status).
    """

    def __init__(self, telegram_client, scheduler):
        """Initialize the plugin manager command handler."""
        super().__init__(telegram_client, scheduler)
        self.admin_chat_id = int(os.getenv('ADMIN_CHAT_ID', '0'))

    def get_handler_type(self) -> str:
        """Return handler type."""
        return "command"

    def get_handler_config(self) -> Dict:
        """Return handler configuration."""
        return {
            'command': 'plugins',
            'description': 'Manage bot plugins'
        }

    def get_plugin_name(self) -> str:
        """Return plugin name."""
        return "plugin_manager"

    def get_description(self) -> str:
        """Return plugin description."""
        return "Plugin management commands (list, enable, disable)"

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle the /plugins command and subcommands.

        Usage:
            /plugins - List all plugins
            /plugins enable <job_id> - Enable a plugin
            /plugins disable <job_id> - Disable a plugin
            /plugins status <job_id> - Show plugin status
        """
        # Check if user is admin
        if update.effective_chat.id != self.admin_chat_id:
            await update.effective_message.reply_text("You are not authorized to use this command.")
            return

        # Parse arguments
        args = context.args if context.args else []

        if len(args) == 0:
            # List all plugins
            await self._list_plugins(update, context)
        elif len(args) == 1:
            await update.effective_message.reply_text(
                "Invalid usage. Try:\n"
                "/plugins - List all plugins\n"
                "/plugins enable <job_id> - Enable a plugin\n"
                "/plugins disable <job_id> - Disable a plugin\n"
                "/plugins status <job_id> - Show plugin status"
            )
        elif len(args) >= 2:
            action = args[0].lower()
            job_id = args[1]

            if action == 'enable':
                await self._enable_plugin(update, context, job_id)
            elif action == 'disable':
                await self._disable_plugin(update, context, job_id)
            elif action == 'status':
                await self._show_status(update, context, job_id)
            else:
                await update.effective_message.reply_text(f"Unknown action: {action}")

    async def _list_plugins(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List all registered plugins."""
        try:
            all_jobs = self.scheduler.job_storage.load_all_jobs()

            if not all_jobs:
                await update.effective_message.reply_text("No plugins registered.")
                return

            # Group by plugin type
            outgoing = []
            incoming = []
            hybrid = []

            for job_data in all_jobs:
                plugin_type = job_data['plugin_type']
                job_id = job_data['job_id']
                active = job_data.get('metadata', {}).get('active', True)
                description = job_data.get('metadata', {}).get('description', 'No description')
                status_icon = "✓" if active else "✗"

                info = f"{status_icon} {job_id}\n   {description}"

                if plugin_type == 'outgoing':
                    outgoing.append(info)
                elif plugin_type == 'incoming':
                    incoming.append(info)
                elif plugin_type == 'hybrid':
                    hybrid.append(info)

            # Build response
            response = "REGISTERED PLUGINS:\n\n"

            if outgoing:
                response += "OUTGOING (Scheduled):\n"
                response += "\n".join(outgoing) + "\n\n"

            if incoming:
                response += "INCOMING (Handlers):\n"
                response += "\n".join(incoming) + "\n\n"

            if hybrid:
                response += "HYBRID (Both):\n"
                response += "\n".join(hybrid) + "\n\n"

            response += "\nUse /plugins status <job_id> for details"

            await update.effective_message.reply_text(response)

        except Exception as e:
            self.logger.error(f"Error listing plugins: {e}")
            await update.effective_message.reply_text(f"Error listing plugins: {e}")

    async def _enable_plugin(self, update: Update, context: ContextTypes.DEFAULT_TYPE, job_id: str):
        """Enable a disabled plugin."""
        try:
            # Load job data
            job_data = self.scheduler.job_storage.load_job(job_id)

            if not job_data:
                await update.effective_message.reply_text(f"Plugin {job_id} not found.")
                return

            # Check if already active
            if job_data.get('metadata', {}).get('active', True):
                await update.effective_message.reply_text(f"Plugin {job_id} is already enabled.")
                return

            # Update metadata
            job_data['metadata']['active'] = True

            # Save updated job data
            self.scheduler.job_storage.save_job(job_data)

            # If it's an outgoing plugin, resume the job in scheduler
            if job_data['plugin_type'] == 'outgoing':
                job = self.scheduler.get_job(job_id)
                if job:
                    job.resume()
                    await update.effective_message.reply_text(f"Plugin {job_id} enabled and resumed.")
                else:
                    await update.effective_message.reply_text(
                        f"Plugin {job_id} enabled in storage but not running in scheduler. "
                        f"Restart the bot to activate it."
                    )
            else:
                await update.effective_message.reply_text(
                    f"Plugin {job_id} enabled. "
                    f"Note: Handler plugins require bot restart to take effect."
                )

        except Exception as e:
            self.logger.error(f"Error enabling plugin {job_id}: {e}")
            await update.effective_message.reply_text(f"Error enabling plugin: {e}")

    async def _disable_plugin(self, update: Update, context: ContextTypes.DEFAULT_TYPE, job_id: str):
        """Disable an enabled plugin."""
        try:
            # Load job data
            job_data = self.scheduler.job_storage.load_job(job_id)

            if not job_data:
                await update.effective_message.reply_text(f"Plugin {job_id} not found.")
                return

            # Check if already inactive
            if not job_data.get('metadata', {}).get('active', True):
                await update.effective_message.reply_text(f"Plugin {job_id} is already disabled.")
                return

            # Update metadata
            job_data['metadata']['active'] = False

            # Save updated job data
            self.scheduler.job_storage.save_job(job_data)

            # If it's an outgoing plugin, pause the job in scheduler
            if job_data['plugin_type'] == 'outgoing':
                job = self.scheduler.get_job(job_id)
                if job:
                    job.pause()
                    await update.effective_message.reply_text(f"Plugin {job_id} disabled and paused.")
                else:
                    await update.effective_message.reply_text(
                        f"Plugin {job_id} disabled in storage but not found in scheduler."
                    )
            else:
                await update.effective_message.reply_text(
                    f"Plugin {job_id} disabled. "
                    f"Note: Handler plugins require bot restart to take effect."
                )

        except Exception as e:
            self.logger.error(f"Error disabling plugin {job_id}: {e}")
            await update.effective_message.reply_text(f"Error disabling plugin: {e}")

    async def _show_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE, job_id: str):
        """Show detailed status of a plugin."""
        try:
            # Load job data
            job_data = self.scheduler.job_storage.load_job(job_id)

            if not job_data:
                await update.effective_message.reply_text(f"Plugin {job_id} not found.")
                return

            # Build status message
            plugin_type = job_data['plugin_type']
            plugin_name = job_data['plugin_name']
            plugin_class = job_data['plugin_class']
            metadata = job_data.get('metadata', {})

            active = metadata.get('active', True)
            status_text = "ENABLED" if active else "DISABLED"

            description = metadata.get('description', 'No description')
            created_at = metadata.get('created_at', 'Unknown')
            exec_count = metadata.get('execution_count', 0)
            last_exec = metadata.get('last_execution', 'Never')
            error_count = metadata.get('error_count', 0)

            response = f"PLUGIN STATUS: {job_id}\n\n"
            response += f"Status: {status_text}\n"
            response += f"Type: {plugin_type.upper()}\n"
            response += f"Class: {plugin_class}\n"
            response += f"Module: {plugin_name}\n"
            response += f"Description: {description}\n\n"
            response += f"Created: {created_at[:19]}\n"
            response += f"Executions: {exec_count}\n"
            response += f"Last run: {last_exec if last_exec != 'Never' else 'Never'}\n"
            response += f"Errors: {error_count}\n"

            # Add schedule info for outgoing plugins
            if plugin_type == 'outgoing':
                schedule = job_data.get('schedule', {})
                trigger = schedule.get('trigger', 'unknown')
                response += f"\nSchedule: {trigger}"

                if trigger == 'interval':
                    if 'minutes' in schedule:
                        response += f" (every {schedule['minutes']} minutes)"
                    elif 'hours' in schedule:
                        response += f" (every {schedule['hours']} hours)"
                    elif 'seconds' in schedule:
                        response += f" (every {schedule['seconds']} seconds)"

                # Check scheduler status
                job = self.scheduler.get_job(job_id)
                if job:
                    next_run = job.next_run_time
                    response += f"\nNext run: {next_run.strftime('%Y-%m-%d %H:%M:%S') if next_run else 'Not scheduled'}"
                else:
                    response += "\nScheduler: Not running"

            await update.effective_message.reply_text(response)

        except Exception as e:
            self.logger.error(f"Error showing status for {job_id}: {e}")
            await update.effective_message.reply_text(f"Error showing status: {e}")
