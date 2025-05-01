from fastapi import APIRouter, Form, UploadFile, Request
from time import time
from typing import Optional


from model.challenges.challenge import Challenge, ChallengeAttempt
from model.api.responses import BaseResponse, ChallengeDefinition
from model.api.requests import AskRequest, VerifyRequest
from ai.llm_handler import LLMHandler
from config.settings import settings
from log.logger import get_logger
from error.exceptions import (
    ChallengeNotFoundError,
    Hack2mException,
    LLMError
)
from core.challenge_service import (
    get_challenge,
    log_attempt,
    challenge_file_agent,
    challenge_code_agent
)

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
    for challenge_id, challenge in settings.CHALLENGES.items():
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
        challenge = await get_challenge("improper-output-handling")
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
    file: Optional[UploadFile] = Form(None, description="File to be uploaded")
) -> BaseResponse:
    """
    Ask a question to the LLM for a specific challenge.

    Args:
        request: AskRequest containing challenge_id, prompt and optional file

    Returns:
        BaseResponse with the LLM's response
    """
    try:
        ask_request = AskRequest(
            challenge_id=challenge_id,
            prompt=prompt,
            file=file
        )
        logger.info(f"Processing ask request for challenge {ask_request.challenge_id}")
        challenge = await get_challenge(ask_request.challenge_id)
        if challenge.id == "indirect-prompt-injection":
            # Security verification for the file (filesize, filetype, etc)
            if request.file.size > 1024 * 1024:
                raise Hack2mException(message="File size is too large")
            if request.file.content_type != "text/plain":
                raise Hack2mException(message="File type is not supported")
            return await challenge_file_agent(ask_request)
        if challenge.id == "excessive-agency":
            return await challenge_code_agent(ask_request)
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
            user_uuid=request.cookies.get("session_id"),
            success=True,
            response=response,
            timestamp=str(time())
        )
        await log_attempt(attempt)

        return BaseResponse(
            message=success_message,
            data={"response": response}
        )
    except ChallengeNotFoundError:
        raise
    except Exception as e:
        logger.exception("Error processing ask request", exc=e)
        raise LLMError("Failed to generate response from LLM")

@router.post("/verify", response_model=BaseResponse)
async def verify_flag(request: VerifyRequest) -> BaseResponse:
    """
    Verify if a submitted flag is correct for a challenge.

    Args:
        challenge_id: ID of the challenge
        flag: Submitted flag to verify

    Returns:
        BaseResponse indicating if the flag is correct
    """
    try:
        logger.info(f"Verifying flag for challenge {request.challenge_id}")
        challenge = await get_challenge(request.challenge_id)

        if request.flag == challenge.flag:
            logger.info(f"Correct flag submitted for challenge {request.challenge_id}")
            return BaseResponse(
                message="Flag is correct! Challenge completed!",
                data={"points": challenge.points}
            )
        else:
            logger.warning(f"Incorrect flag submitted for challenge {request.challenge_id}")
            return BaseResponse(
                success=False,
                message="Flag is incorrect",
                data={}
            )
    except ChallengeNotFoundError:
        raise
    except Exception as e:
        logger.exception("Error verifying flag", exc=e)
        raise LLMError("Failed to verify flag")
