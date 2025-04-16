from fastapi import APIRouter
from model.challenge import (
    Challenge,
    ChallengeResponse,
    ChallengeAttempt,
    AskRequest
)
from ai.llm_handler import LLMHandler
from config.challenges import get_challenge
from log.logger import get_logger
from error.exceptions import (
    ChallengeNotFoundError,
    LLMError,
    InvalidFlagError
)
import time

router = APIRouter()
logger = get_logger("challenge")

def _get_challenge(challenge_id: str) -> Challenge:
    """Get challenge configuration by ID."""
    try:
        return get_challenge(challenge_id)
    except ValueError as e:
        logger.warning(f"Challenge not found: {challenge_id}")
        raise ChallengeNotFoundError(challenge_id)
    except Exception as e:
        logger.exception("Error getting challenge", exc=e)
        raise

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
        logger.info(f"Processing ask request for challenge {request.challenge_id}")
        challenge = _get_challenge(request.challenge_id)

        llm_handler = LLMHandler.get_instance()
        # Generate response
        response = llm_handler.generate(
            prompt=request.prompt,
            system_prompt=challenge.system_prompt,
            max_tokens=challenge.requirements.max_tokens,
            #temperature=challenge.requirements.temperature
        )

        # Log attempt
        attempt = ChallengeAttempt(
            challenge_id=request.challenge_id,
            user_id=request.user_id,
            prompt=request.prompt,
            success=True,
            response=response,
            timestamp=str(time.time())
        )
        _log_attempt(attempt)

        return ChallengeResponse(
            success=True,
            message="Challenge response generated successfully",
            data={"response": response}
        )
    except ChallengeNotFoundError:
        raise
    except Exception as e:
        logger.exception("Error processing ask request", exc=e)
        raise LLMError("Failed to generate response from LLM")

@router.post("/verify", response_model=ChallengeResponse)
async def verify_flag(
    challenge_id: str,
    flag: str,
    user_id: str
) -> ChallengeResponse:
    """
    Verify if a submitted flag is correct for a challenge.

    Args:
        challenge_id: ID of the challenge
        flag: Submitted flag to verify
        user_id: ID of the user submitting the flag

    Returns:
        ChallengeResponse indicating if the flag is correct
    """
    try:
        logger.info(f"Verifying flag for challenge {challenge_id}")
        challenge = _get_challenge(challenge_id)

        if flag == challenge.flag:
            logger.info(f"Correct flag submitted for challenge {challenge_id}")
            return ChallengeResponse(
                success=True,
                message="Flag is correct! Challenge completed!",
                data={"points": challenge.points}
            )
        else:
            logger.warning(f"Incorrect flag submitted for challenge {challenge_id}")
            raise InvalidFlagError("Incorrect flag format or value")
    except ChallengeNotFoundError:
        raise
    except Exception as e:
        logger.exception("Error verifying flag", exc=e)
        raise LLMError("Failed to verify flag")

def _log_attempt(attempt: ChallengeAttempt) -> None:
    """Log a challenge attempt."""
    logger.info(
        f"Challenge attempt logged: {attempt.challenge_id} by user {attempt.user_id}"
    )
