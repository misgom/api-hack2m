from asyncpg import Connection
from fastapi import status
from os import path, remove
import asyncio
import re
import subprocess

from ai.llm_handler import LLMHandler
from config.settings import settings
from error.exceptions import Hack2mException, ChallengeNotFoundError
from log.logger import get_logger
from model.api.requests import AskRequest
from model.challenges.challenge import ChallengeAttempt, Challenge


logger = get_logger("challenge_service")

class ChallengeService:
    """Challenge service class to handle challenge-related operations."""

    def __init__(self, db: Connection):
        self.challenges = settings.CHALLENGES
        self.db = db

    async def get_challenge(self, challenge_id: str) -> Challenge:
        """Get challenge configuration by ID."""
        try:
            # Create a copy of the challenge to avoid modifying the original
            challenge = Challenge(**self.challenges[challenge_id].model_dump())
            challenge_flag = challenge.system_prompt.format(flag=challenge.flag)
            challenge.system_prompt = challenge_flag
            return challenge
        except KeyError as e:
            logger.warning(f"Challenge not found: {challenge_id}")
            raise ChallengeNotFoundError(challenge_id)
        except Exception as e:
            logger.exception("Error getting challenge", exc=e)
            raise


    async def log_attempt(self, attempt: ChallengeAttempt) -> None:
        """Log a challenge attempt."""
        logger.info(
            f"Challenge attempt logged: {attempt.challenge_id} by user {attempt.user_uuid}"
        )

    async def challenge_code_agent(self, request: AskRequest) -> str:
        """Challenge code agent."""
        challenge = await self.get_challenge("excessive-agency")
        llm_handler = LLMHandler.get_instance()
        # Generate response
        full_prompt = await llm_handler.generate(
            prompt=request.prompt,
            system_prompt=challenge.system_prompt,
            max_tokens=challenge.requirements.max_tokens,
            full_response=True
        )
        response = full_prompt[-1].get("content")
        match = re.search(r"# SCRIPT\s+(.*)", response, re.DOTALL)
        if match:
            code = match.group(1).strip()

            result_output = await self.execute_code(code, challenge.flag)
            logger.info(f"Result output: {result_output}")

            # New generation, with the result as context
            #followup_prompt = list[dict](**full_prompt)

            full_prompt[-1]["content"] = (
                full_prompt[-1]["content"].replace("# SCRIPT", "# SCRIPT\n```python\n")
                + f"```\n# RESULT\n{result_output}"
            )
            final_response = await llm_handler.generate_chat(
                messages=full_prompt,
                max_tokens=challenge.requirements.max_tokens,
                #full_response=True
            )

            return final_response

        else:
            # No code detected, return initial output
            return full_prompt[-1].get("content")

    async def execute_code(self, code: str, flag: str) -> str:
        code_filename = settings.CODE_FILENAME
        flag_filename = settings.FLAG_FILENAME

        with open(code_filename, "w") as f:
            f.write(code)
        with open(flag_filename, "w") as f:
            f.write(flag)

        try:
            # Execute docker container with the code
            container_name = "exec"
            result = await asyncio.to_thread(subprocess.run, [
                "docker", "run",
                "--rm",
                "--name", container_name,
                "--memory", "100m",
                "--cpus", "0.2",
                "--read-only",
                "--network=none",
                "--volume", f"{code_filename}:/home/xuser/code.py:ro",
                "--volume", f"{flag_filename}:/home/xuser/flag.txt:ro",
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
            # Clean up files
            if path.exists(code_filename):
                remove(code_filename)
            if path.exists(flag_filename):
                remove(flag_filename)

    async def challenge_file_agent(self, request: AskRequest) -> str:
        """Challenge file agent."""
        challenge = await self.get_challenge("indirect-prompt-injection")
        llm_handler = LLMHandler.get_instance()

        # Read the file
        file_content = await request.file.read()
        # Generate response
        response = await llm_handler.generate(
            prompt=file_content,
            system_prompt=challenge.system_prompt,
            max_tokens=challenge.requirements.max_tokens
        )

        return response
