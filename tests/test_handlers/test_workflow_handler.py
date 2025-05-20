"""Tests for workflow_handler.py"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, CallbackQuery, Message, Chat, User
from telegram.ext import ContextTypes
from ai_gym_bro.handlers.workflow_handler import (
    received_goal,
    process_refinement_input,
    AWAITING_REFINEMENT_CHOICE,
    ConversationHandler,
)
from ai_gym_bro.handlers.common import (
    USER_DATA_GOAL,
    USER_DATA_PLAN,
    USER_DATA_HISTORY,
    USER_DATA_REFINEMENT_TYPE,
    POWERLIFTING,
    ASK_QUESTION_CALLBACK,
    MODIFY_PLAN_CALLBACK,
)

# Test data
TEST_USER_DATA = {
    "age": "25",
    "height": "174",
    "weight": "100",
    "squat": "170",
    "bench": "145",
    "deadlift": "200",
    "injuries": "no",
    "goal": POWERLIFTING,
}

@pytest.fixture
def mock_update():
    """Create a mock Update object."""
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock(spec=User)
    update.effective_user.id = 123456
    update.effective_chat = MagicMock(spec=Chat)
    update.effective_chat.id = 123456
    return update

@pytest.fixture
def mock_context():
    """Create a mock Context object."""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}
    context.bot = MagicMock()
    context.bot.send_message = AsyncMock()
    return context

@pytest.fixture
def mock_callback_query():
    """Create a mock CallbackQuery object."""
    query = MagicMock(spec=CallbackQuery)
    query.data = POWERLIFTING
    query.answer = AsyncMock()
    query.edit_message_text = AsyncMock()
    return query

@pytest.fixture
def mock_message():
    """Create a mock Message object."""
    message = MagicMock(spec=Message)
    message.text = "Can you modify the plan to include more deadlift volume?"
    message.reply_text = AsyncMock()
    return message

@pytest.mark.asyncio
async def test_received_goal_success(mock_update, mock_context, mock_callback_query):
    """Test successful goal selection and plan generation."""
    # Setup
    mock_update.callback_query = mock_callback_query
    mock_context.user_data.update(TEST_USER_DATA)
    
    # Mock the openai_service response
    mock_plan = "Your personalized powerlifting plan:\nWeek 1: ..."
    mock_history = [{"role": "assistant", "content": mock_plan}]
    
    with patch("ai_gym_bro.handlers.workflow_handler.openai_service.generate_plan") as mock_generate:
        mock_generate.return_value = (mock_plan, mock_history)
        
        # Execute
        result = await received_goal(mock_update, mock_context)
        
        # Verify
        assert result == AWAITING_REFINEMENT_CHOICE
        assert mock_context.user_data[USER_DATA_GOAL] == POWERLIFTING
        assert mock_context.user_data[USER_DATA_PLAN] == mock_plan
        assert mock_context.user_data[USER_DATA_HISTORY] == mock_history
        
        # Verify bot interactions
        mock_callback_query.answer.assert_called_once()
        mock_callback_query.edit_message_text.assert_called_once()
        assert mock_context.bot.send_message.call_count >= 2  # Plan message + options message

@pytest.mark.asyncio
async def test_received_goal_failure(mock_update, mock_context, mock_callback_query):
    """Test goal selection with failed plan generation."""
    # Setup
    mock_update.callback_query = mock_callback_query
    mock_context.user_data.update(TEST_USER_DATA)
    
    # Mock the openai_service failure
    with patch("ai_gym_bro.handlers.workflow_handler.openai_service.generate_plan") as mock_generate:
        mock_generate.return_value = (None, None)
        
        # Execute
        result = await received_goal(mock_update, mock_context)
        
        # Verify
        assert result == ConversationHandler.END
        assert not mock_context.user_data  # Should be cleared on failure
        mock_context.bot.send_message.assert_called_once()

@pytest.mark.asyncio
async def test_process_refinement_input_success(mock_update, mock_context, mock_message):
    """Test successful refinement request processing."""
    # Setup
    mock_update.message = mock_message
    mock_context.user_data.update({
        USER_DATA_HISTORY: [{"role": "assistant", "content": "Initial plan"}],
        USER_DATA_REFINEMENT_TYPE: "modify"
    })
    
    # Mock the openai_service response
    mock_response = "I've modified the plan to include more deadlift volume..."
    mock_new_history = [
        {"role": "assistant", "content": "Initial plan"},
        {"role": "user", "content": mock_message.text},
        {"role": "assistant", "content": mock_response}
    ]
    
    with patch("ai_gym_bro.handlers.workflow_handler.openai_service.refine_plan") as mock_refine:
        mock_refine.return_value = (mock_response, mock_new_history)
        
        # Execute
        result = await process_refinement_input(mock_update, mock_context)
        
        # Verify
        assert result == AWAITING_REFINEMENT_CHOICE
        assert mock_context.user_data[USER_DATA_HISTORY] == mock_new_history
        # Check that reply_text was called at least twice:
        # 1. For "Got it. Thinking about your request... 🤔"
        # 2. For the response
        # 3. For "What would you like to do next?"
        assert mock_message.reply_text.call_count >= 3

@pytest.mark.asyncio
async def test_process_refinement_input_no_history(mock_update, mock_context, mock_message):
    """Test refinement request with missing history."""
    # Setup
    mock_update.message = mock_message
    mock_context.user_data.update({
        USER_DATA_REFINEMENT_TYPE: "modify"
    })  # No history
    
    # Execute
    result = await process_refinement_input(mock_update, mock_context)
    
    # Verify
    assert result == ConversationHandler.END
    assert not mock_context.user_data  # Should be cleared
    mock_message.reply_text.assert_called_once()

@pytest.mark.asyncio
async def test_process_refinement_input_failure(mock_update, mock_context, mock_message):
    """Test refinement request with failed processing."""
    # Setup
    mock_update.message = mock_message
    mock_context.user_data.update({
        USER_DATA_HISTORY: [{"role": "assistant", "content": "Initial plan"}],
        USER_DATA_REFINEMENT_TYPE: "modify"
    })
    
    # Mock the openai_service failure
    with patch("ai_gym_bro.handlers.workflow_handler.openai_service.refine_plan") as mock_refine:
        mock_refine.return_value = (None, None)
        
        # Execute
        result = await process_refinement_input(mock_update, mock_context)
        
        # Verify
        assert result == AWAITING_REFINEMENT_CHOICE  # Should return to choice state
        # Check that reply_text was called at least twice:
        # 1. For "Got it. Thinking about your request... 🤔"
        # 2. For the error message with options
        assert mock_message.reply_text.call_count >= 2 