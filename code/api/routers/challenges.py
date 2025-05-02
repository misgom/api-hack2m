from asyncpg import Connection
from fastapi import APIRouter, Depends, Form, Request, UploadFile
from time import time
from typing import Optional

from ai.llm_handler import LLMHandler
from config.settings import settings
from core.challenge_service import ChallengeService
from core.score_service import ScoreService
from database import get_connection
from error.exceptions import (
    ChallengeNotFoundError,
    Hack2mException,
    LLMError
)
from log.logger import get_logger
from model.challenges.challenge import ChallengeAttempt
from model.api.responses import BaseResponse, ChallengeDefinition
from model.api.requests import AskRequest, VerifyRequest

router = APIRouter()
logger = get_logger("challenge")
success_message = "Challenge response generated successfully"

@router.get("/challenge-definitions", response_model=BaseResponse)
async def challenge_definitions() -> BaseResponse:
    """
    Get all challenge definitions.

    Returns:
        BaseResponse with the list of challenge definitions
    """
    challenges = []
    for challenge in settings.CHALLENGES.values():
        challenges.append(ChallengeDefinition(**challenge.model_dump()))
    return BaseResponse(
        message="Challenge definitions retrieved successfully",
        data={"challenges": challenges}
    )

@router.get("/xss")
async def xss_challenge() -> str:
    """
    Get the XSS challenge flag.

    Returns:
        BaseResponse with the XSS challenge definition
    """
    try:
        challenge = await challenge_service.get_challenge("improper-output-handling")
        return challenge.flag
    except ChallengeNotFoundError:
        raise
    except Exception as e:
        logger.exception("Error retrieving XSS challenge", exc=e)
        raise Hack2mException("Failed to retrieve XSS challenge")

@router.post("/ask", response_model=BaseResponse)
async def ask_challenge(
    request: Request,
    challenge_id: str = Form(..., description="ID of the challenge"),
    prompt: str = Form(..., description="User's input prompt"),
    file: Optional[UploadFile] = Form(None, description="File to be uploaded"),
    db: Connection = Depends(get_connection)
) -> BaseResponse:
    """
    Ask a question to the LLM for a specific challenge.

    Args:
        request: AskRequest containing challenge_id, prompt and optional file

    Returns:
        BaseResponse with the LLM's response
    """
    try:
        challenge_service = ChallengeService(db)
        score_service = ScoreService(db)

        ask_request = AskRequest(
            challenge_id=challenge_id,
            prompt=prompt,
            file=file
        )
        logger.info(f"Processing ask request for challenge {ask_request.challenge_id}")

        # Get the challenge
        challenge = await challenge_service.get_challenge(ask_request.challenge_id)

        # Record the attempt and update score
        session_id = request.cookies.get("session_id")
        user_id = None  # TODO: Get from auth token when implemented
        await score_service.record_attempt(challenge.uuid, challenge.points, user_id, session_id)

        if challenge.id == "indirect-prompt-injection":
            # Security verification for the file (filesize, filetype, etc)
            if file.size > 1024 * 1024:
                raise Hack2mException(message="File size is too large")
            if file.content_type != "text/plain":
                raise Hack2mException(message="File type is not supported")
            result = await challenge_service.challenge_file_agent(ask_request)
            return BaseResponse(message=success_message, data={"response": result})

        if challenge.id == "excessive-agency":
            result = await challenge_service.challenge_code_agent(ask_request)
            return BaseResponse(message=success_message, data={"response": result})

        llm_handler = LLMHandler.get_instance()
        # Generate response
        response = await llm_handler.generate(
            prompt=ask_request.prompt,
            system_prompt=challenge.system_prompt,
            max_tokens=challenge.requirements.max_tokens
        )

        # Log attempt
        attempt = ChallengeAttempt(
            challenge_id=ask_request.challenge_id,
            prompt=ask_request.prompt,
            user_uuid=session_id,
            success=True,
            response=response,
            timestamp=str(time())
        )
        await challenge_service.log_attempt(attempt)

        return BaseResponse(
            message="Response generated successfully",
            data={"response": response}
        )
    except ChallengeNotFoundError:
        raise
    except Exception as e:
        logger.exception("Error processing ask request", exc=e)
        raise LLMError("Failed to generate response from LLM")

@router.post("/verify", response_model=BaseResponse)
async def verify_flag(
    request: Request,
    verify_request: VerifyRequest,
    db: Connection = Depends(get_connection)
) -> BaseResponse:
    """
    Verify a flag for a challenge.

    Args:
        request: Request object
        challenge_id: ID of the challenge
        flag: Flag to verify

    Returns:
        BaseResponse with success status
    """
    try:
        challenge_service = ChallengeService(db)
        score_service = ScoreService(db)

        # Get the challenge
        challenge = await challenge_service.get_challenge(verify_request.challenge_id)

        # Verify the flag
        if verify_request.flag.strip() != challenge.flag:
            # Record failed flag attempt
            session_id = request.cookies.get("session_id")
            user_id = None  # TODO: Get from auth token when implemented
            await score_service.record_failed_flag_attempt(challenge.uuid, challenge.points, user_id, session_id)
            raise Hack2mException(message="Invalid flag")

        # Record completion
        session_id = request.cookies.get("session_id")
        user_id = None  # TODO: Get from auth token when implemented
        final_score = await score_service.record_completion(challenge.uuid, challenge.points, user_id, session_id)

        return BaseResponse(
            message="Flag verified successfully",
            data={"score": final_score}
        )
    except ChallengeNotFoundError:
        raise
    except Exception as e:
        logger.exception("Error verifying flag", exc=e)
        raise Hack2mException(message="Failed to verify flag")
