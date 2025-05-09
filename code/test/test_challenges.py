from fastapi.testclient import TestClient
from main import app
from model.challenge import Challenge, ChallengeDifficulty
import pytest

client = TestClient(app)

def test_ask_challenge():
    """Test the ask endpoint for challenges."""
    response = client.post(
        "/api/challenges/ask",
        json={
            "challenge_id": "1",
            "prompt": "test prompt",
            "user_id": "test_user"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert "message" in data
    assert "data" in data

def test_verify_flag():
    """Test the verify endpoint for challenges."""
    response = client.post(
        "/api/challenges/verify",
        json={
            "challenge_id": "1",
            "flag": "CTF{test_flag}",
            "user_id": "test_user"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert "message" in data

def test_challenge_model():
    """Test the Challenge model."""
    challenge = Challenge(
        id="1",
        title="Test Challenge",
        description="Test description",
        difficulty=ChallengeDifficulty.EASY,
        points=100,
        system_prompt="Test system prompt",
        flag="CTF{test_flag}",
        example_prompt="Test example prompt"
    )
    assert challenge.id == "1"
    assert challenge.title == "Test Challenge"
    assert challenge.difficulty == ChallengeDifficulty.EASY
    assert challenge.points == 100

@pytest.mark.asyncio
async def test_llm_handler():
    """Test the LLM handler."""
    from ai.llm_handler import LLMHandler
    from config.settings import Settings

    settings = Settings()
    handler = LLMHandler.get_instance()

    # Test response generation
    response = handler.generate_response(
        prompt="test prompt",
        system_prompt="test system prompt"
    )
    assert isinstance(response, str)

    # Test flag checking
    assert handler.check_flag("CTF{test_flag}", "CTF{test_flag}") is True
    assert handler.check_flag("wrong flag", "CTF{test_flag}") is False
