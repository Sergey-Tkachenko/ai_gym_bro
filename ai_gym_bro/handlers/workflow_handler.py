"""Handles the multi-step conversation workflow for plan generation."""

from loguru import logger
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from ai_gym_bro.services import openai_service # Use the alias
from ai_gym_bro.handlers.common import (
    ASK_AGE, ASK_HEIGHT, ASK_WEIGHT, ASK_EXPERIENCE, ASK_SQUAT, ASK_BENCH,
    ASK_DEADLIFT, ASK_INJURIES, SELECT_GOAL, GENERATING_PLAN,
    AWAITING_REFINEMENT_CHOICE, AWAITING_REFINEMENT_INPUT, # Updated states
    GOAL_OPTIONS, HYPERTROPHY, POWERLIFTING,
    ASK_QUESTION_CALLBACK, MODIFY_PLAN_CALLBACK, # Refinement callback data
    USER_DATA_AGE, USER_DATA_HEIGHT, USER_DATA_WEIGHT, USER_DATA_EXPERIENCE,
    USER_DATA_SQUAT, USER_DATA_BENCH, USER_DATA_DEADLIFT, USER_DATA_INJURIES,
    USER_DATA_GOAL, USER_DATA_PLAN, USER_DATA_HISTORY, USER_DATA_REFINEMENT_TYPE # New user data key
)
from ai_gym_bro.handlers.start_handler import start, cancel # Import start for entry point, cancel for fallback

# --- Helper Functions ---

async def _ask_next_question(update: Update, context: ContextTypes.DEFAULT_TYPE, question: str, next_state: int) -> int:
    """Helper to ask a question and return the next state."""
    # Check if update.message exists (for text input) or update.callback_query (for button clicks)
    if update.message:
        await update.message.reply_text(question)
    elif update.callback_query:
        # If coming from a button, edit the message to ask the next question
        await update.callback_query.edit_message_text(question)
    else:
        logger.warning("Update type not handled in _ask_next_question")
        # Fallback if update type is unexpected
        if update.effective_chat:
           await context.bot.send_message(chat_id=update.effective_chat.id, text=question)

    return next_state

async def _store_and_advance(
    update: Update, context: ContextTypes.DEFAULT_TYPE, key: str, question: str, next_state: int
) -> int:
    """Helper to store user text input and ask the next question."""
    user_input = update.message.text
    context.user_data[key] = user_input
    logger.debug(f"User {update.effective_user.id}: Stored {key} = {user_input}")
    return await _ask_next_question(update, context, question, next_state)

# --- State Handler Functions ---

async def received_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores age and asks for height."""
    return await _store_and_advance(
        update, context, USER_DATA_AGE, "Got it. What is your height (e.g., cm or ft/in)?", ASK_HEIGHT
    )

async def received_height(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores height and asks for weight."""
    return await _store_and_advance(
        update, context, USER_DATA_HEIGHT, "Thanks. And your current weight (e.g., kg or lbs)?", ASK_WEIGHT
    )

async def received_weight(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores weight and asks for experience."""
    return await _store_and_advance(
        update, context, USER_DATA_WEIGHT, "What is your resistance training experience level (e.g., beginner, intermediate, advanced)?", ASK_EXPERIENCE
    )

async def received_experience(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores experience and asks for squat max."""
    return await _store_and_advance(
        update, context, USER_DATA_EXPERIENCE, "What is your current estimated 1 Rep Max (1RM) or recent best set for Squat?", ASK_SQUAT
    )

async def received_squat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores squat max and asks for bench max."""
    return await _store_and_advance(
        update, context, USER_DATA_SQUAT, "Okay. How about your Bench Press 1RM or best set?", ASK_BENCH
    )

async def received_bench(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores bench max and asks for deadlift max."""
    return await _store_and_advance(
        update, context, USER_DATA_BENCH, "And your Deadlift 1RM or best set?", ASK_DEADLIFT
    )

async def received_deadlift(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores deadlift max and asks for injuries."""
    return await _store_and_advance(
        update, context, USER_DATA_DEADLIFT, "Do you have any current injuries or physical limitations I should be aware of? (Type 'None' if not)", ASK_INJURIES
    )

async def received_injuries(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores injuries and asks for training goal."""
    user_input = update.message.text
    context.user_data[USER_DATA_INJURIES] = user_input
    logger.debug(f"User {update.effective_user.id}: Stored {USER_DATA_INJURIES} = {user_input}")

    keyboard = [
        [InlineKeyboardButton(HYPERTROPHY, callback_data=HYPERTROPHY)],
        [InlineKeyboardButton(POWERLIFTING, callback_data=POWERLIFTING)],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Finally, what is your primary training goal?", reply_markup=reply_markup)
    return SELECT_GOAL

async def received_goal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the selected goal, starts plan generation, presents plan and asks for refinement choice."""
    query = update.callback_query
    await query.answer() # Acknowledge callback
    goal = query.data
    context.user_data[USER_DATA_GOAL] = goal
    logger.info(f"User {update.effective_user.id}: Selected goal {goal}")

    await query.edit_message_text(text=f"Great! Goal selected: {goal}.\n\nGenerating your personalized plan now... This might take a moment. 🧠")

    # --- Plan Generation --- (Transition happens here implicitly)
    try:
        user_info = context.user_data.copy() # Get collected data
        plan = await openai_service.generate_plan(user_info)

        if plan:
            context.user_data[USER_DATA_PLAN] = plan
            # Initialize history for refinement
            context.user_data[USER_DATA_HISTORY] = [
                {"role": "user", "content": f"My profile: Age={user_info.get(USER_DATA_AGE)}, Height={user_info.get(USER_DATA_HEIGHT)}, Weight={user_info.get(USER_DATA_WEIGHT)}, Experience={user_info.get(USER_DATA_EXPERIENCE)}, Squat={user_info.get(USER_DATA_SQUAT)}, Bench={user_info.get(USER_DATA_BENCH)}, Deadlift={user_info.get(USER_DATA_DEADLIFT)}, Injuries={user_info.get(USER_DATA_INJURIES)}, Goal={user_info.get(USER_DATA_GOAL)}"},
                {"role": "assistant", "content": plan}
            ]

            await context.bot.send_message(chat_id=update.effective_chat.id, text="Here is your initial workout plan:")
            # Send plan in chunks if too long (Telegram limit is 4096 chars)
            # Simple chunking for now
            for i in range(0, len(plan), 4000):
                await context.bot.send_message(chat_id=update.effective_chat.id, text=plan[i:i+4000])

            # Present refinement options
            keyboard = [
                [InlineKeyboardButton("❓ Ask a Question", callback_data=ASK_QUESTION_CALLBACK)],
                [InlineKeyboardButton("✏️ Suggest Modification", callback_data=MODIFY_PLAN_CALLBACK)],
                [InlineKeyboardButton("🏁 Finish (Cancel)", callback_data="cancel_refinement")] # Option to exit loop
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="What would you like to do next?",
                reply_markup=reply_markup
            )
            return AWAITING_REFINEMENT_CHOICE # Go to new state
        else:
            logger.error(f"Plan generation failed for user {update.effective_user.id}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Sorry, I encountered an error trying to generate your plan. Please try again later by sending /start."
            )
            context.user_data.clear()
            return ConversationHandler.END

    except Exception as e:
        logger.exception(f"Exception during plan generation for user {update.effective_user.id}: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="An unexpected error occurred during plan generation. Please try /start again."
        )
        context.user_data.clear()
        return ConversationHandler.END

# New handler for refinement choice buttons
async def received_refinement_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the user's choice between asking a question or suggesting modification."""
    query = update.callback_query
    await query.answer()
    choice = query.data

    if choice == ASK_QUESTION_CALLBACK:
        logger.info(f"User {update.effective_user.id} chose to ask a question.")
        context.user_data[USER_DATA_REFINEMENT_TYPE] = 'ask'
        await query.edit_message_text(text="Okay, please type your question about the plan.")
        return AWAITING_REFINEMENT_INPUT
    elif choice == MODIFY_PLAN_CALLBACK:
        logger.info(f"User {update.effective_user.id} chose to suggest modification.")
        context.user_data[USER_DATA_REFINEMENT_TYPE] = 'modify'
        await query.edit_message_text(text="Okay, please describe the modification you'd like to suggest.")
        return AWAITING_REFINEMENT_INPUT
    elif choice == "cancel_refinement":
        logger.info(f"User {update.effective_user.id} chose to finish refinement.")
        await query.edit_message_text(text="Got it. Plan finalized! Send /start to create a new one.")
        # Keep user_data for potential future reference? Or clear?
        # context.user_data.clear() # Optional: clear if conversation is truly done
        return ConversationHandler.END
    else:
        logger.warning(f"Received unexpected callback data in refinement choice: {choice}")
        await query.edit_message_text(text="Sorry, something went wrong. Please try again or use /cancel.")
        # Stay in the same state or end? Let's stay for now.
        return AWAITING_REFINEMENT_CHOICE

# Renamed from received_refinement_request
async def process_refinement_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles user's text input for refinement/questions after choice."""
    user_request = update.message.text
    user = update.effective_user
    refinement_type = context.user_data.get(USER_DATA_REFINEMENT_TYPE, 'unknown')
    logger.info(f"User {user.id} refinement input (type: {refinement_type}): {user_request}")

    if USER_DATA_HISTORY not in context.user_data or not context.user_data[USER_DATA_HISTORY]:
        logger.warning(f"User {user.id} in refinement state but no history found.")
        await update.message.reply_text("Something went wrong, I don't have the context. Please start over with /start.")
        context.user_data.clear()
        return ConversationHandler.END

    history = context.user_data[USER_DATA_HISTORY]
    # Add context about the type of request for the LLM?
    # E.g.: history.append({"role": "user", "content": f"My request ({refinement_type}): {user_request}"})
    # For now, just add the raw request:
    history.append({"role": "user", "content": user_request})

    await update.message.reply_text("Got it. Thinking about your request... 🤔")

    try:
        response = await openai_service.refine_plan(history, user_request)

        if response:
            # Check response length for Telegram
            if len(response) > 4096:
                logger.warning("Refinement response exceeds Telegram limit. Sending truncated.")
                response_part = response[:4000] + "... (response truncated)"
            else:
                response_part = response

            history.append({"role": "assistant", "content": response_part}) # Store potentially truncated response in history?
            context.user_data[USER_DATA_HISTORY] = history # Update history
            # Note: We might want to update USER_DATA_PLAN if the response implies a full plan change
            # For MVP, we just show the response.
            await update.message.reply_text(response_part)

            # Go back to asking for choice
            keyboard = [
                [InlineKeyboardButton("❓ Ask Another Question", callback_data=ASK_QUESTION_CALLBACK)],
                [InlineKeyboardButton("✏️ Suggest Another Modification", callback_data=MODIFY_PLAN_CALLBACK)],
                [InlineKeyboardButton("🏁 Finish (Cancel)", callback_data="cancel_refinement")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "What would you like to do next?",
                reply_markup=reply_markup
            )
            return AWAITING_REFINEMENT_CHOICE # Loop back to choice state
        else:
            logger.error(f"Plan refinement failed for user {user.id}")
            # Go back to asking for choice after failure?
            keyboard = [
                [InlineKeyboardButton("❓ Try Asking Question", callback_data=ASK_QUESTION_CALLBACK)],
                [InlineKeyboardButton("✏️ Try Suggesting Modification", callback_data=MODIFY_PLAN_CALLBACK)],
                [InlineKeyboardButton("🏁 Cancel", callback_data="cancel_refinement")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "Sorry, I couldn't process that request. Try rephrasing or choose an option:",
                reply_markup=reply_markup
            )
            return AWAITING_REFINEMENT_CHOICE # Loop back to choice state even on failure

    except Exception as e:
        logger.exception(f"Exception during plan refinement for user {user.id}: {e}")
        # Go back to asking for choice after exception?
        keyboard = [
            [InlineKeyboardButton("❓ Try Asking Question", callback_data=ASK_QUESTION_CALLBACK)],
            [InlineKeyboardButton("✏️ Try Suggesting Modification", callback_data=MODIFY_PLAN_CALLBACK)],
            [InlineKeyboardButton("🏁 Cancel", callback_data="cancel_refinement")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "An unexpected error occurred. Please try again or choose an option:",
            reply_markup=reply_markup
        )
        return AWAITING_REFINEMENT_CHOICE # Loop back to choice state on exception

async def unknown_state_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles messages received in an unexpected state or with unexpected commands."""
    logger.warning(f"Received unexpected message/command in conversation from user {update.effective_user.id}")
    await update.message.reply_text(
        "Sorry, I wasn't expecting that. If you're stuck, you can try /cancel and start over with /start."
    )

# --- Conversation Handler Definition ---

def create_workflow_handler() -> ConversationHandler:
    """Creates the ConversationHandler for the main workflow."""
    return ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^/start$"), start)], # Use start from start_handler as entry
        states={
            ASK_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_age)],
            ASK_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_height)],
            ASK_WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_weight)],
            ASK_EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_experience)],
            ASK_SQUAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_squat)],
            ASK_BENCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_bench)],
            ASK_DEADLIFT: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_deadlift)],
            ASK_INJURIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_injuries)],
            SELECT_GOAL: [CallbackQueryHandler(received_goal)],
            # Note: GENERATING_PLAN is a transient state handled within received_goal
            AWAITING_REFINEMENT_CHOICE: [
                CallbackQueryHandler(received_refinement_choice, pattern=f"^({ASK_QUESTION_CALLBACK}|{MODIFY_PLAN_CALLBACK}|cancel_refinement)$")
                # Add MessageHandler here? Or handle unexpected text via fallback?
            ],
            AWAITING_REFINEMENT_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_refinement_input)
            ],
        },
        fallbacks=[
            MessageHandler(filters.Regex("^/cancel$"), cancel), # Use cancel from start_handler
            CallbackQueryHandler(cancel, pattern="^cancel_refinement$"), # Handle cancel button from refinement choice
            MessageHandler(filters.COMMAND, unknown_state_handler), # Handle unexpected commands
            MessageHandler(filters.ALL, unknown_state_handler)      # Handle unexpected message types
        ],
        per_message=False, # Process messages based on state, not one handler per message
        # name="plan_workflow", # Optional: Name for debugging
        # persistent=True # Handled by Application builder persistence
    ) 