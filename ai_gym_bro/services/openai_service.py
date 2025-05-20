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
TEMPERATURE = 0.7  # Adjust for creativity vs determinism

MAX_TOKENS_PLAN = 2500  # Adjust as needed for plan length
MAX_TOKENS_REFINEMENT = 2500 # Adjust as needed for refinement responses

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

**Программа на 5 недель с периодизацией**  
- **Beginner/Intermediate:** 3 дня в неделю  
- **Advanced:** 5 дней в неделю  

**Структура каждого тренировочного дня (Markdown):**

**Разминка:**  
Упражнение 1 — повторения\\подходы  
Упражнение 2 — повторения\\подходы  
…

**Основная часть:**  
Упражнение 1 — подходы×повторы×интенсивность (Неделя 1 / Неделя 2 / … / Неделя 5)  
Упражнение 2 — подходы×повторы×интенсивность (Неделя 1 / Неделя 2 / … / Неделя 5)  
…

**Вспомогательные упражнения:**  
Упражнение 1 — подходы×повторы  
Упражнение 2 — подходы×повторы  
…

**Инструкции:** 
1. Анализируйте возраст, рост, вес, опыт, уровень (1RM) и травмы только для оценки уровня — в плане используйте **только проценты**.
2. По цели:
   - **Набор мышечной массы:** 8–12 повторений, умеренные веса (65-75% от 1RM), больше базовых упражнений.
   - **Уменьшение жировой массы:** 12–15 повторений, умеренные веса (60-70% от 1RM), больше кардио и суперсетов.
3. Для каждого упражнения дайте таблицу или маркированный список:
   - Неделя 1: X % × Y подходов × Z повторений
   - …
   - Неделя 5: X % × Y подходов × Z повторений
4. Учитывайте травмы и предлагайте альтернативы.
5. Тон — профессиональный, мотивирующий, без вступлений/заключений.
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
