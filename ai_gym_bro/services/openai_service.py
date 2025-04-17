"""Service layer for interacting with OpenAI API."""

import os
import asyncio
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from loguru import logger
from openai import AsyncOpenAI, OpenAIError # Import necessary parts

# --- Constants --- #
MODEL_NAME = "gpt-4o-mini"
MAX_TOKENS_PLAN = 1500 # Adjust as needed for plan length
MAX_TOKENS_REFINEMENT = 500 # Adjust as needed for refinement responses
TEMPERATURE = 0.7 # Adjust for creativity vs determinism

# --- Load API Key --- #
load_dotenv(override=True) # Ensure environment variables are loaded
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    logger.critical("OPENAI_API_KEY environment variable not found!")
    # Decide how to handle this - exit, raise error, or run in limited mode?
    # For now, we'll log a critical error. The functions below will fail.
    # raise ValueError("Missing OPENAI_API_KEY")

# --- Initialize Async Client --- #
# Initialize only if API_KEY is present
aclient = AsyncOpenAI(api_key=API_KEY) if API_KEY else None

# --- System Prompts (Consider moving to config/YAML later) --- #
SYSTEM_PROMPT_PLAN_GENERATION = f"""
You are an expert Strength and Conditioning coach specializing in creating personalized workout plans for resistance training athletes using Telegram.

Your task is to generate a detailed, weekly workout plan based *strictly* on the user's provided information and their primary goal (Hypertrophy or Powerlifting).

**Instructions:**
1.  **Analyze User Data:** Carefully consider the user's age, height, weight, experience level, current strength levels (squat, bench, deadlift 1RMs or recent bests), and any mentioned injuries/limitations.
2.  **Select Goal Focus:**
    *   **Hypertrophy:** Prioritize exercises, set/rep schemes (e.g., 3-5 sets of 8-15 reps), and potentially techniques known to induce muscle growth. Include accessory movements.
    *   **Powerlifting:** Focus on improving the squat, bench press, and deadlift. Structure the plan around these lifts (e.g., using percentages of 1RM, lower reps like 3-6), and include relevant accessory work for strength.
3.  **Structure:** Provide a clear weekly schedule (e.g., Day 1, Day 2, Rest, Day 3...). For each workout day, list exercises with specific sets, reps, and suggested rest times. If possible, provide guidance on selecting appropriate weights based on their provided strength levels (e.g., "Work up to a heavy set of 5" or "Use a weight you can perform 10 reps with").
4.  **Injuries:** Account for mentioned injuries. Either suggest alternative exercises or advise caution around specific movements. If an injury significantly impacts a core lift for their goal, acknowledge this limitation.
5.  **Format:** Use Markdown for clear formatting (bolding exercises, bullet points for sets/reps).
6.  **Tone:** Be encouraging, knowledgeable, and professional.
7.  **Conciseness:** Generate the plan directly without introductory or concluding pleasantries beyond the structured plan itself. The plan should fit within Telegram message limits (aim for under {MAX_TOKENS_PLAN} tokens).
"""

SYSTEM_PROMPT_REFINEMENT = f"""
You are an expert Strength and Conditioning coach assistant helping a user refine or understand their generated workout plan.

You will receive the conversation history, including the user's initial profile, the generated plan, and previous interactions.

The last message in the history is the user's current request (question or modification suggestion).

**Instructions:**
1.  **Context is Key:** Base your response *entirely* on the provided conversation history and the user's latest request.
2.  **Address the Request:**
    *   **Questions:** Answer the user's question about the plan clearly and concisely, referencing specific parts of the plan if necessary.
    *   **Modifications:** Acknowledge the suggested modification. If feasible and safe, explain how the plan could be adjusted (provide specific changes). If the modification is not advisable (e.g., unsafe, counterproductive to the goal), explain why and offer alternatives if possible.
3.  **Safety First:** Do not suggest modifications that could compromise safety based on the user's profile or stated injuries.
4.  **Tone:** Maintain an encouraging, knowledgeable, and helpful tone.
5.  **Conciseness:** Keep responses focused and relatively brief (aim for under {MAX_TOKENS_REFINEMENT} tokens) suitable for Telegram.
"""

# --- Service Functions --- #

async def generate_plan(user_data: Dict[str, Any]) -> Optional[str]:
    """Generates a workout plan using the OpenAI API."""
    if not aclient:
        logger.error("OpenAI client not initialized. Cannot generate plan.")
        return "Error: OpenAI client not configured."

    logger.info(f"Requesting plan generation for user data: {user_data}")

    # Format user data into a message for the prompt
    user_profile_summary = f"""
    Here is the user's information:
    - Age: {user_data.get('age', 'N/A')}
    - Height: {user_data.get('height', 'N/A')}
    - Weight: {user_data.get('weight', 'N/A')}
    - Experience: {user_data.get('experience', 'N/A')}
    - Squat (1RM or best set): {user_data.get('squat', 'N/A')}
    - Bench Press (1RM or best set): {user_data.get('bench', 'N/A')}
    - Deadlift (1RM or best set): {user_data.get('deadlift', 'N/A')}
    - Injuries/Limitations: {user_data.get('injuries', 'None specified')}
    - Primary Goal: {user_data.get('goal', 'N/A')}
    """

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_PLAN_GENERATION},
        {"role": "user", "content": user_profile_summary}
    ]

    try:
        response = await aclient.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS_PLAN,
            timeout=120,
        )
        plan = response.choices[0].message.content
        logger.info("Plan generated successfully by OpenAI.")
        logger.debug(f"OpenAI Response: {response}") # Log full response for debugging
        return plan.strip() if plan else None

    except OpenAIError as e:
        logger.error(f"OpenAI API error during plan generation: {e}")
        return None
    except Exception as e:
        logger.exception(f"Unexpected error during plan generation: {e}")
        return None


async def refine_plan(history: List[Dict[str, str]], user_request: str) -> Optional[str]:
    """Refines or answers questions about a plan using the OpenAI API and history."""
    # Note: user_request is already appended to history by the handler

    if not aclient:
        logger.error("OpenAI client not initialized. Cannot refine plan.")
        return "Error: OpenAI client not configured."

    logger.info(f"Requesting plan refinement based on history. Last user request: {user_request}")
    logger.debug(f"History sent to OpenAI: {history}")

    # Construct messages for the API call
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_REFINEMENT}
    ] + history # Add the full history

    try:
        response = await aclient.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS_REFINEMENT,
            timeout=120,
        )
        refinement_response = response.choices[0].message.content
        logger.info("Plan refinement/answer generated successfully by OpenAI.")
        logger.debug(f"OpenAI Response: {response}")
        return refinement_response.strip() if refinement_response else None

    except OpenAIError as e:
        logger.error(f"OpenAI API error during plan refinement: {e}")
        return None
    except Exception as e:
        logger.exception(f"Unexpected error during plan refinement: {e}")
        return None 