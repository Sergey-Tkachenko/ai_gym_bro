"""Common constants and utilities for handlers."""

# Conversation states
(
    ASK_AGE,
    ASK_HEIGHT,
    ASK_WEIGHT,
    ASK_EXPERIENCE,
    ASK_BENCH,
    ASK_INJURIES,
    SELECT_GOAL,
    GENERATING_PLAN,
    AWAITING_REFINEMENT_CHOICE,
    AWAITING_REFINEMENT_INPUT,
) = range(10) # Updated range

# Goal options
MUSCLE_GAIN = "Набор мышечной массы"
FAT_LOSS = "Уменьшение жировой массы"
GOAL_OPTIONS = [MUSCLE_GAIN, FAT_LOSS]

# User data keys (for context.user_data)
USER_DATA_AGE = "age"
USER_DATA_HEIGHT = "height"
USER_DATA_WEIGHT = "weight"
USER_DATA_EXPERIENCE = "experience"
USER_DATA_BENCH = "bench"
USER_DATA_INJURIES = "injuries"
USER_DATA_GOAL = "goal"
USER_DATA_PLAN = "plan"
USER_DATA_HISTORY = "history" # To store conversation for refinement
USER_DATA_REFINEMENT_TYPE = "refinement_type" # New key: 'ask' or 'modify'

# Refinement choice options (callback data)
ASK_QUESTION_CALLBACK = "refine_ask"
MODIFY_PLAN_CALLBACK = "refine_modify"

# Define command descriptions
COMMAND_DESCRIPTIONS = {
    "start": "Start interaction and plan generation workflow",
    "help": "Show available commands and bot description",
    "cancel": "Cancel the current operation/conversation",
}

# Training plan instructions
TRAINING_PLAN_INSTRUCTIONS = (
    "📋 *Как читать план тренировок:*\n\n"
    "1. *Разминка:*\n"
    "   - Упражнение — подходы×повторы\n"
    "   - Например: «Приседания — 3×12» означает 3 подхода по 12 повторений\n\n"
    "2. *Основная часть:*\n"
    "   - Формат: подходы×повторы×интенсивность (Неделя 1 / Неделя 2 / ... / Неделя 5)\n"
    "   - Например: «3×12×70% (70/75/80/75/70)» означает:\n"
    "     • 3 подхода по 12 повторений\n"
    "     • Интенсивность по неделям: 70% / 75% / 80% / 75% / 70% от вашего максимума\n\n"
    "3. *Вспомогательные упражнения:*\n"
    "   - Формат: подходы×повторы\n"
    "   - Например: «3×15» означает 3 подхода по 15 повторений\n\n"
    "Вы всегда можете увидеть эти инструкции, выполнив команду /help"
)