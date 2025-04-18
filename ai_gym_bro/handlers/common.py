"""Common constants and utilities for handlers."""

# Conversation states
(
    ASK_AGE,
    ASK_HEIGHT,
    ASK_WEIGHT,
    ASK_EXPERIENCE,
    ASK_SQUAT,
    ASK_BENCH,
    ASK_DEADLIFT,
    ASK_INJURIES,
    SELECT_GOAL,
    GENERATING_PLAN,
    REFINING_PLAN,
) = range(11) # Use range for simplicity

# Goal options
HYPERTROPHY = "Hypertrophy"
POWERLIFTING = "Powerlifting"
GOAL_OPTIONS = [HYPERTROPHY, POWERLIFTING]

# User data keys (for context.user_data)
USER_DATA_AGE = "age"
USER_DATA_HEIGHT = "height"
USER_DATA_WEIGHT = "weight"
USER_DATA_EXPERIENCE = "experience"
USER_DATA_SQUAT = "squat"
USER_DATA_BENCH = "bench"
USER_DATA_DEADLIFT = "deadlift"
USER_DATA_INJURIES = "injuries"
USER_DATA_GOAL = "goal"
USER_DATA_PLAN = "plan"
USER_DATA_HISTORY = "history" # To store conversation for refinement 


# Define command descriptions
COMMAND_DESCRIPTIONS = {
    "start": "Start interaction and plan generation workflow",
    "help": "Show available commands and bot description",
    "cancel": "Cancel the current operation/conversation",
}