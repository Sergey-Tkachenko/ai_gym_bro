"""Service layer for interacting with OpenAI API (or mocks)."""

import asyncio
from typing import Any, Dict, List, Optional
from loguru import logger

# Mock implementations for MVP
async def generate_plan(user_data: Dict[str, Any]) -> Optional[str]:
    """Generates a workout plan based on user data (mocked)."""
    logger.info(f"Generating mock plan for user data: {user_data}")
    await asyncio.sleep(2) # Simulate API call delay

    # Basic check for essential data for the mock
    required_keys = [
        'age', 'height', 'weight', 'experience',
        'squat', 'bench', 'deadlift', 'injuries', 'goal'
    ]
    if not all(key in user_data for key in required_keys):
        logger.warning("Missing some user data for mock plan generation.")
        # In a real scenario, might return None or raise error

    plan = f"""
    **Mock Workout Plan for {user_data.get('goal', 'Unknown Goal')}**

    *Goal:* {user_data.get('goal', 'N/A')}
    *Experience:* {user_data.get('experience', 'N/A')}
    *Notes on Injuries:* {user_data.get('injuries', 'None specified')}

    **Day 1: Push**
    - Bench Press: 3 sets of 5 reps (based on {user_data.get('bench', 'N/A')})
    - Overhead Press: 3 sets of 8 reps
    - Tricep Extensions: 3 sets of 12 reps

    **Day 2: Pull**
    - Deadlift: 1 set of 5 reps (based on {user_data.get('deadlift', 'N/A')})
    - Pull-ups/Lat Pulldowns: 3 sets of 8-10 reps
    - Barbell Rows: 3 sets of 10 reps

    **Day 3: Legs**
    - Squat: 3 sets of 5 reps (based on {user_data.get('squat', 'N/A')})
    - Leg Press: 3 sets of 12 reps
    - Hamstring Curls: 3 sets of 15 reps

    *Disclaimer: This is a mocked plan. Consult a professional.*
    """
    logger.info("Mock plan generated.")
    return plan

async def refine_plan(history: List[Dict[str, str]], user_request: str) -> Optional[str]:
    """Refines or answers questions about a plan based on history (mocked)."""
    logger.info(f"Refining mock plan based on request: {user_request}")
    logger.debug(f"History context (mock): {history}")
    await asyncio.sleep(1) # Simulate API call delay

    if "more volume" in user_request.lower():
        response = "Mock Refinement: Okay, let's add one more set to your main lifts."
    elif "less intensity" in user_request.lower():
        response = "Mock Refinement: Understood. We can reduce the target reps by 1-2 on heavy sets."
    elif "explain" in user_request.lower():
        response = "Mock Answer: This exercise targets your posterior chain, which is crucial for... (mock explanation)"
    else:
        response = f"Mock Response: Acknowledged your request: '{user_request}'. I'll adjust the plan accordingly (mock adjustment)."

    logger.info("Mock refinement/answer generated.")
    return response 