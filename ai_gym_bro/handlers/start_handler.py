"""Handlers for basic commands like /start, /help, /cancel."""

from loguru import logger
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from ai_gym_bro.handlers.common import (
    ASK_AGE, # Import the first state of the conversation
    COMMAND_DESCRIPTIONS # Assuming you might define this centrally later
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks for the first piece of info (age)."""
    user = update.effective_user
    logger.info(f"User {user.id} ({user.username}) started interaction.")
    context.user_data.clear() # Clear data from previous sessions

    await update.message.reply_html(
        f"Hi {user.mention_html()}! I'm your AI Gym Bro. 💪\n\n"
        f"I need some information to create your personalized workout plan. "
        f"Let's start with your age.\n\n"
        f"You can type /cancel at any time to stop."
    )
    await update.message.reply_text("How old are you?")

    return ASK_AGE # Transition to the first state


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = "🤖 *AI Gym Bro Commands*\n\n"
    help_text += "I can help you generate a personalized workout plan!\n\n"

    # Add each command and its description
    for command, description in COMMAND_DESCRIPTIONS.items():
        help_text += f"/{command} - {description}\n"

    help_text += "\nUse /help to see this message again."

    await update.message.reply_text(help_text, parse_mode="Markdown")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.effective_user
    logger.info(f"User {user.id} ({user.username}) canceled the conversation.")
    await update.message.reply_text(
        "Okay, operation cancelled. Talk to you later! Send /start if you change your mind."
    )
    context.user_data.clear()
    return ConversationHandler.END 