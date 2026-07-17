import sys
import os
backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_path)

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from datetime import datetime

import models.user
import models.products
import models.invoice
import models.ai
import models.auth

from app import app
from db.database import get_async_db
from middlewares.auth import auth, current_user
from models.ai import ChatMessage as ChatMessageModel

db_mock = None

async def override_get_async_db():
    yield db_mock

def mock_current_user():
    return 10

app.dependency_overrides[get_async_db] = override_get_async_db
app.dependency_overrides[current_user] = mock_current_user

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_db_mock():
    global db_mock
    db_mock = AsyncMock()
    app.dependency_overrides[get_async_db] = override_get_async_db
    app.dependency_overrides[current_user] = mock_current_user
    yield
    app.dependency_overrides.clear()

def mock_db_result(value=None):
    mock_res = MagicMock()
    if isinstance(value, list):
        mock_res.scalars.return_value.all.return_value = value
        mock_res.all.return_value = value
    else:
        mock_res.scalar_one_or_none.return_value = value
        mock_res.scalar_one.return_value = value
    return mock_res

@patch("routes.ai.chat_with_agent")
def test_integration_chat_with_agent(mock_chat):
    mock_chat.return_value = ChatMessageModel(
        id=1,
        business_id=1,
        user_id=10,
        session_id="session123",
        sender="assistant",
        message="Hello! I am your AI assistant.",
        created_at=datetime.utcnow()
    )
    
    response = client.post(
        "/ai/chat?business_id=1",
        json={"message": "hello", "session_id": "session123"}
    )
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["session_id"] == "session123"
    assert res_data["message"] == "Hello! I am your AI assistant."
    mock_chat.assert_called_once()
