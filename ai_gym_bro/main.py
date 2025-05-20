"""Main entry point for the Telegram bot."""

import os
from pathlib import Path

from loguru import logger
from telegram import Update
from telegram.ext import (
    Application,
    ContextTypes,
    PicklePersistence,
    CommandHandler,
)
from dotenv import load_dotenv

# Import handlers
from ai_gym_bro.handlers import start_handler, workflow_handler


async def post_init(application: Application) -> None:
    """Sets the bot commands after initialization."""
    commands = [
        (command, description)
        for command, description in start_handler.COMMAND_DESCRIPTIONS.items()
    ]
    await application.bot.set_my_commands(commands)
    logger.info("Bot commands set.")


def main() -> None:
    """Starts the bot."""
    load_dotenv() # Load environment variables from .env file

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set!")
        return

    # Setup persistence
    persistence_path = Path(__file__).parent / "persistence" / "bot_persistence.pkl"
    persistence_path.parent.mkdir(parents=True, exist_ok=True) # Ensure directory exists
    logger.info(f"Using persistence file: {persistence_path}")
    persistence = PicklePersistence(filepath=persistence_path)

    # Create the Application
    application = (
        Application.builder()
        .token(bot_token)
        .persistence(persistence)
        .post_init(post_init) # Set commands after setup
        .build()
    )

    # Add top-level command handlers first (like /help)
    application.add_handler(CommandHandler("help", start_handler.help_command))

    # Create and add the main workflow handler
    conv_handler = workflow_handler.create_workflow_handler()
    application.add_handler(conv_handler)

    # Configure logging for PTB
    # logging.basicConfig( # Handled by Loguru setup potentially
    #     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
    # )
    # logging.getLogger("httpx").setLevel(logging.WARNING)
    logger.info("Starting bot polling...")

    # Start the Bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    # Configure Loguru
    logger.add(
        "ai_gym_bro.log",
        rotation="10 MB",
        level="DEBUG", # Log debug messages to file
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
    )
    logger.add(
        lambda msg: print(msg, end=""), # Log info to console
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
    )
    main()
