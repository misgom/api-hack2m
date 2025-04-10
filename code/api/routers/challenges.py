from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from model.challenge import Challenge, ChallengeResponse, ChallengeAttempt, AskRequest
from ai.llm_handler import LLMHandler
from config.settings import Settings
import time

router = APIRouter()
settings = Settings()

@router.post("/ask", response_model=ChallengeResponse)
async def ask_challenge(request: AskRequest) -> ChallengeResponse:
    """
    Ask a question to the LLM for a specific challenge.

    Args:
        request: AskRequest containing challenge_id, prompt, and user_id

    Returns:
        ChallengeResponse with the LLM's response
    """
    try:
        # Get challenge configuration
        challenge = _get_challenge(request.challenge_id)

        llm_handler = LLMHandler.get_instance()
        # Generate response
        response = llm_handler.generate(
            prompt=request.prompt,
            system_prompt=challenge.system_prompt,
            max_tokens=challenge.requirements.max_tokens,
            temperature=challenge.requirements.temperature
        )

        # Log attempt
        attempt = ChallengeAttempt(
            challenge_id=request.challenge_id,
            user_id=request.user_id,
            prompt=request.prompt,
            response=response,
            success=llm_handler.check_flag(response, challenge.flag),
            timestamp=str(time.time())
        )
        _log_attempt(attempt)

        return ChallengeResponse(
            success=True,
            message="Response generated successfully",
            data={"response": response}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify", response_model=ChallengeResponse)
async def verify_flag(
    challenge_id: str,
    flag: str,
    user_id: str
) -> ChallengeResponse:
    """
    Verify if a submitted flag is correct.

    Args:
        challenge_id: ID of the challenge
        flag: Submitted flag
        user_id: ID of the user

    Returns:
        ChallengeResponse indicating if the flag is correct
    """
    try:
        challenge = _get_challenge(challenge_id)

        if flag == challenge.flag:
            return ChallengeResponse(
                success=True,
                message="Flag is correct!",
                data={"points": challenge.points}
            )
        else:
            return ChallengeResponse(
                success=False,
                message="Incorrect flag",
                data=None
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _get_challenge(challenge_id: str) -> Challenge:
    """Get challenge configuration by ID."""
    # TODO: Implement challenge retrieval from database
    pass

def _log_attempt(attempt: ChallengeAttempt) -> None:
    """Log a challenge attempt."""
    # TODO: Implement attempt logging
    pass
