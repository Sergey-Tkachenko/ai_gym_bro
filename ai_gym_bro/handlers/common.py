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
HYPERTROPHY = "Hypertrophy"
POWERLIFTING = "Powerlifting"
GOAL_OPTIONS = [HYPERTROPHY, POWERLIFTING]

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