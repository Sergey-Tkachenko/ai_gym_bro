"""Service layer for interacting with OpenAI API."""

import os
import asyncio
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from loguru import logger
from langfuse.openai import AsyncOpenAI
from openai import OpenAIError

# --- Constants --- #
MODEL_NAME = "gpt-4.1"
MAX_TOKENS_PLAN = 1000  # Adjust as needed for plan length
MAX_TOKENS_REFINEMENT = 1000  # Adjust as needed for refinement responses
TEMPERATURE = 0.7  # Adjust for creativity vs determinism

# --- Load API Key --- #
load_dotenv(override=True)  # Ensure environment variables are loaded
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
You think in English but output entirely in Russian.

**Общая структура:**
- 5-недельная программа с периодизацией: для каждого упражнения указывайте % от 1RM, кол-во подходов и повторений для каждой из 5 недель.
- В зависимости от опыта:
  - **Beginner/Intermediate:** 3 трен-дня в неделю.
  - **Advanced:** 5 трен-дней в неделю.
- Формат дней: «День 1», «День 2» … «День 5» (если нужно).
- Разделы каждого дня:
  1. **Разминка** (2–3 упражнения)
  2. **Основные упражнения** (3–5 движений)
  3. **Вспомогательные упражнения** (2–4 движения)

**Инструкции:**
1. Анализируйте возраст, рост, вес, опыт, уровень (1RM) и травмы только для оценки уровня — в плане используйте **только проценты**.
2. По цели:
   - **Гипертрофия:** 8–15 повторений.
   - **Пауэрлифтинг:** 3–6 повторений.
3. Для каждого упражнения дайте таблицу или маркированный список:
   - Неделя 1: X % × Y подходов × Z повторений
   - …
   - Неделя 5: X % × Y подходов × Z повторений
4. Учитывайте травмы и предлагайте альтернативы.
5. Тон — профессиональный, мотивирующий, без вступлений/заключений.
6. Поместить в Markdown, уложиться в {MAX_TOKENS_PLAN} токенов.
"""


SYSTEM_PROMPT_REFINEMENT = f"""
You are an expert Strength & Conditioning ассистент, отвечаете на вопросы и вносите правки в уже сгенерированный план.

Вам дано:
- История переписки и текущий план (на русском, в Markdown).
- Последний запрос пользователя.

**Действуйте так:**
1. Опирайтесь только на историю и последний запрос.
2. Если пользователь спрашивает — отвечайте конкретно, ссылаясь на разделы плана.
3. Если просит изменить — предложите безопасные правки (конкретные упражнения/подходы).
4. Тон — поддерживающий и профессиональный.
5. Ответ на русском, в Markdown, в пределах {MAX_TOKENS_REFINEMENT} токенов.
"""

# --- Service Functions --- #


async def generate_plan(user_data: Dict[str, Any]) -> Optional[Tuple[str, List[Dict[str, str]]]]:
    """
    Generates a workout plan using the OpenAI API.
    Returns the plan string and the initial list of messages for history.
    """
    if not aclient:
        logger.error("OpenAI client not initialized. Cannot generate plan.")
        # Return a tuple indicating error, and empty history
        return ("Error: OpenAI client not configured.", [])

    logger.info(f"Requesting plan generation for user data: {user_data}")

    # Format user data into a message for the prompt
    user_profile_summary = f"""
    При создании плана строго следуйте данным пользователя:
    - Возраст: {user_data.get("age", "N/A")}
    - Рост: {user_data.get("height", "N/A")}
    - Вес: {user_data.get("weight", "N/A")}
    - Опыт: {user_data.get("experience", "N/A")}
    - Жим лежа (1RM или лучший результат): {user_data.get("bench", "N/A")}
    - Травмы/ограничения: {user_data.get("injuries", "None specified")}
    - Цель: {user_data.get("goal", "N/A")}
"""

    # initial_messages will be part of the history
    initial_messages = [
        {"role": "system", "content": SYSTEM_PROMPT_PLAN_GENERATION},
        {"role": "system", "content": user_profile_summary},
    ]

    try:
        response = await aclient.chat.completions.create(
            model=MODEL_NAME,
            messages=initial_messages,  # Use initial_messages here
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS_PLAN,
            timeout=120,
        )
        plan_content = response.choices[0].message.content
        logger.info("Plan generated successfully by OpenAI.")
        logger.debug(f"OpenAI Response: {response}")

        if plan_content:
            plan_str = plan_content.strip()
            # Append assistant's response to the messages for history
            history_for_refinement = initial_messages + [{"role": "assistant", "content": plan_str}]
            return plan_str, history_for_refinement
        else:
            return None, []  # Return None for plan and empty history

    except OpenAIError as e:
        logger.error(f"OpenAI API error during plan generation: {e}")
        return None, []
    except Exception as e:
        logger.exception(f"Unexpected error during plan generation: {e}")
        return None, []


async def refine_plan(history: List[Dict[str, str]]) -> Optional[str]:
    """Refines or answers questions about a plan using the OpenAI API and history."""
    if not aclient:
        logger.error("OpenAI client not initialized. Cannot refine plan.")
        return "Error: OpenAI client not configured."

    # The last message in history is the current user_request
    if not history or history[-1]["role"] != "user":
        logger.error("History is empty or last message is not from user for refinement.")
        return "Error: Invalid history state for refinement."

    logger.info(f"Requesting plan refinement. Last user request: {history[-1]['content']}")
    logger.debug(f"Full history sent to OpenAI for refinement: {history}")

    # Construct messages for the API call - system prompt must be first
    # messages_for_api = history + [{"role": "system", "content": SYSTEM_PROMPT_REFINEMENT}]

    try:
        response = await aclient.chat.completions.create(
            model=MODEL_NAME,
            messages=history,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS_REFINEMENT,
            timeout=120,
        )
        refinement_response = response.choices[0].message.content
        logger.info("Plan refinement/answer generated successfully by OpenAI.")
        logger.debug(f"OpenAI Response: {response}")

        refinement_response = refinement_response.strip() if refinement_response else None

        if refinement_response:
            history.append({"role": "assistant", "content": refinement_response})
            return refinement_response, history
        else:
            return None, history

    except OpenAIError as e:
        logger.error(f"OpenAI API error during plan refinement: {e}")
        return None
    except Exception as e:
        logger.exception(f"Unexpected error during plan refinement: {e}")
        return None
