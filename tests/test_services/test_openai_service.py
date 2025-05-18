"""Tests for the OpenAI service layer, including API connectivity."""

import os
import pytest
from dotenv import load_dotenv
from langfuse.openai import AsyncOpenAI
from openai import OpenAIError

# Load environment variables for the test
load_dotenv(override=True)

# Mark all tests in this module as async
pytestmark = pytest.mark.asyncio

# Conditionally skip tests if API key is missing
API_KEY = os.getenv("OPENAI_API_KEY")
REASON = "OPENAI_API_KEY environment variable not set or invalid."


@pytest.mark.skipif(not API_KEY or "YOUR_OPENAI_API_KEY_HERE" in API_KEY, reason=REASON)
async def test_openai_api_connectivity_and_auth():
    """Tests basic connectivity and authentication with the OpenAI API.

    This test makes a real, simple API call. It will be skipped if
    the OPENAI_API_KEY environment variable is not set or contains the
    placeholder value.
    Requires a VALID API key to be configured in the environment.
    """
    print(f"\nAttempting OpenAI API connectivity test with key ending in ...{API_KEY[-4:] if API_KEY else 'N/A'}")
    aclient = None
    try:
        aclient = AsyncOpenAI(api_key=API_KEY)
        # Use a minimal chat completion call to verify auth and connectivity
        response = await aclient.chat.completions.create(
            model="gpt-4o-mini",  # Or another cheap model if preferred
            messages=[{"role": "user", "content": "Hello!"}],
            max_tokens=10,  # Keep it very short
            temperature=0,  # Minimal creativity needed
        )

        # Basic assertion: Check if the call succeeded and we got some data
        assert response is not None
        assert len(response.choices) > 0
        assert response.choices[0].message is not None
        assert response.choices[0].message.content is not None
        assert len(response.choices[0].message.content) > 0  # Ensure we got some response text
        print("OpenAI API connectivity and authentication successful.")

    except OpenAIError as e:
        pytest.fail(f"OpenAI API error during connectivity test: {e}")
    except Exception as e:
        pytest.fail(f"Unexpected error during OpenAI connectivity test: {e}")
    finally:
        if aclient:
            await aclient.close()


# Placeholder for testing the generate_plan function (likely with mocks)
async def test_generate_plan_mocked():
    """Placeholder for testing generate_plan logic with mocked API calls."""
    # TODO: Implement test using mocks (e.g., pytest-asyncio, unittest.mock)
    assert True


# Placeholder for testing the refine_plan function (likely with mocks)
async def test_refine_plan_mocked():
    """Placeholder for testing refine_plan logic with mocked API calls."""
    # TODO: Implement test using mocks
    assert True
