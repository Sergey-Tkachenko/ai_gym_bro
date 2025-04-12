"""Main entry point for the Telegram bot."""

import logging
import os

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Command descriptions
COMMAND_DESCRIPTIONS = {
    "start": "Start the bot and get a welcome message",
    "help": "Show this help message with all available commands",
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(f"Hi {user.mention_html()}! I'm your AI Gym Bro. How can I help you today?")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = "🤖 *AI Gym Bro Commands*\n\n"

    # Add each command and its description
    for command, description in COMMAND_DESCRIPTIONS.items():
        help_text += f"/{command} - {description}\n"

    help_text += "\nUse /help to see this message again."

    await update.message.reply_text(help_text, parse_mode="Markdown")


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token
    application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Start the Bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
