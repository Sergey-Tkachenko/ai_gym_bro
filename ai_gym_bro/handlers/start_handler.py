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
        f"Привет {user.mention_html()}! Я твой AI Gym Bro. 💪\n\n"
        f"Мне нужна некоторая информация, чтобы создать твой персональный план тренировок. "
        f"Давай начнем с твоего возраста.\n\n"
        f"В любой момент ты можешь написать /cancel, чтобы остановиться."
    )
    await update.message.reply_text("Сколько тебе лет?")

    return ASK_AGE # Transition to the first state


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = "🤖 *Команды AI Gym Bro*\n\n"
    help_text += "Я могу помочь тебе создать персональный план тренировок!\n\n"

    # Add each command and its description
    for command, description in COMMAND_DESCRIPTIONS.items():
        help_text += f"/{command} - {description}\n"

    help_text += "\nИспользуй /help, чтобы снова увидеть это сообщение."

    await update.message.reply_text(help_text, parse_mode="Markdown")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.effective_user
    logger.info(f"User {user.id} ({user.username}) canceled the conversation.")
    await update.message.reply_text(
        "Хорошо, операция отменена. До встречи! Напиши /start, если передумаешь."
    )
    context.user_data.clear()
    return ConversationHandler.END 