from fastapi import APIRouter, status
from os import path, remove
from model.challenge import (
    Challenge,
    ChallengeResponse,
    ChallengeAttempt,
    AskRequest,
    VerifyRequest,
    ChallengeDefinitionsResponse
)
from ai.llm_handler import LLMHandler
from config.settings import settings
from log.logger import get_logger
from error.exceptions import (
    ChallengeNotFoundError,
    Hack2mException,
    LLMError,
    InvalidFlagError
)
import time
import re
import subprocess

router = APIRouter()
logger = get_logger("challenge")
success_message = "Challenge response generated successfully"

@router.get("/challenge-definitions", response_model=ChallengeResponse)
async def challenge_definitions() -> ChallengeResponse:
    """
    Get all challenge definitions.

    Returns:
        ChallengeResponse with the list of challenge definitions
    """
    challenges = []
    for challenge_id, challenge in settings.CHALLENGES.items():
        challenges.append(Challenge(**challenge.model_dump()))
    return ChallengeResponse(
        success=True,
        message="Challenge definitions retrieved successfully",
        data={"challenges": challenges}
    )

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
        if challenge.id == "challenge-06":
            return _challenge_code_agent(request)
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
            message=success_message,
            data={"response": response}
        )
    except ChallengeNotFoundError:
        raise
    except Exception as e:
        logger.exception("Error processing ask request", exc=e)
        raise LLMError("Failed to generate response from LLM")

@router.post("/verify", response_model=ChallengeResponse)
async def verify_flag(request: VerifyRequest) -> ChallengeResponse:
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
        logger.info(f"Verifying flag for challenge {request.challenge_id}")
        challenge = _get_challenge(request.challenge_id)

        if request.flag == challenge.flag:
            logger.info(f"Correct flag submitted for challenge {request.challenge_id}")
            return ChallengeResponse(
                success=True,
                message="Flag is correct! Challenge completed!",
                data={"points": challenge.points}
            )
        else:
            logger.warning(f"Incorrect flag submitted for challenge {request.challenge_id}")
            return ChallengeResponse(
                success=False,
                message="Flag is incorrect",
                data={}
            )
    except ChallengeNotFoundError:
        raise
    except Exception as e:
        logger.exception("Error verifying flag", exc=e)
        raise LLMError("Failed to verify flag")

def _get_challenge(challenge_id: str) -> Challenge:
    """Get challenge configuration by ID."""
    try:
        # Create a copy of the challenge to avoid modifying the original
        challenge = Challenge(**settings.CHALLENGES[challenge_id].model_dump())
        challenge_flag = challenge.system_prompt.format(flag=challenge.flag)
        challenge.system_prompt = challenge_flag
        return challenge
    except KeyError as e:
        logger.warning(f"Challenge not found: {challenge_id}")
        raise ChallengeNotFoundError(challenge_id)
    except Exception as e:
        logger.exception("Error getting challenge", exc=e)
        raise

def _log_attempt(attempt: ChallengeAttempt) -> None:
    """Log a challenge attempt."""
    logger.info(
        f"Challenge attempt logged: {attempt.challenge_id} by user {attempt.user_id}"
    )

def _challenge_code_agent(request: AskRequest) -> ChallengeResponse:
    """Challenge code agent."""
    challenge = _get_challenge("challenge-06")
    llm_handler = LLMHandler.get_instance()
    # Generate response
    full_prompt = llm_handler.generate(
        prompt=request.prompt,
        system_prompt=challenge.system_prompt,
        max_tokens=challenge.requirements.max_tokens,
        full_response=True
    )
    response = full_prompt[-1].get("content")
    match = re.search(r"#EXECUTE\s+(.*)", response, re.DOTALL)
    if match:
        code = match.group(1).strip()

        result_output = _execute_code(code, challenge.flag)
        logger.info(f"Result output: {result_output}")

        # New generation, with the result as context
        #followup_prompt = list[dict](**full_prompt)
        full_prompt[-1]["content"] += f"\n#RESULT\n{result_output}"

        final_response = llm_handler.generate_chat(
            messages=full_prompt,
            max_tokens=challenge.requirements.max_tokens,
            #full_response=True
        )

        return ChallengeResponse(
            success=True,
            message=success_message,
            data={"response": final_response}
        )

    else:
        # No code detected, return initial output
        return ChallengeResponse(
            success=True,
            message=success_message,
            data={"response": full_prompt[-1].get("content")}
        )

def _execute_code(code: str, flag: str) -> str:
    code_filename = "code.py"
    flag_filename = "flag.txt"
    with open(code_filename, "w") as f:
        f.write(code)
    with open(flag_filename, "w") as f:
        f.write(flag)

    try:
        # Ejecutar contenedor docker
        container_name = "exec"
        result = subprocess.run([
            "docker", "run",
            "--rm",
            "--name", container_name,
            "--memory", "100m",
            "--cpus", "0.2",
            "--read-only",
            "--network=none",
            "--volume", f".\\{code_filename}:/home/xuser/code.py:ro",
            "--volume", f".\\{flag_filename}:/home/xuser/flag.txt:ro",
            settings.DOCKER_IMAGE
        ], capture_output=True, text=True, timeout=10)

        return result.stdout or result.stderr or ""

    except subprocess.TimeoutExpired:
        logger.warning("Timeout exceeded while executing code")
        raise Hack2mException(
            "Timeout exceeded while executing code",
            status_code=status.HTTP_408_REQUEST_TIMEOUT
        )
    except Exception as e:
        logger.exception("Error while executing code", exc=e)
        raise Hack2mException("Error while executing code")

    finally:
        # Limpiar
        if path.exists(code_filename):
            remove(code_filename)
        if path.exists(flag_filename):
            remove(flag_filename)
