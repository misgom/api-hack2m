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

@router.get("/leaderboard", response_model=BaseResponse)
async def get_leaderboard(db: Connection = Depends(get_connection)) -> BaseResponse:
    """Get leaderboard endpoint

    Args:
        db (Connection, optional): the db connection. Defaults to Depends(get_connection).

    Returns:
        BaseResponse: the response with the leaderboard
    """
    score_service = ScoreService(db)

    leaderboard = await score_service.get_leaderboard()

    return BaseResponse(
        message="Leaderboard succesfully retrieved",
        data={"leaderboard": leaderboard}
    )

@router.get("/score", response_model=BaseResponse)
async def get_score(
    request: Request,
    db: Connection = Depends(get_connection)
) -> BaseResponse:
    """Get score endpoint

    Args:
        challenge_id (str): the challenge id
        user_id (Optional[str], optional): the user id. Defaults to None.
        session_id (Optional[str], optional): the session id. Defaults to None.
        db (Connection, optional): the db connection. Defaults to Depends(get_connection).

    Raises:
        Hack2mException: if the challenge is not found

    Returns:
        BaseResponse: the response with the score
    """
    score_service = ScoreService(db)

    session_id = request.cookies.get("session_id")
    user_id = None  # TODO: Get from auth token when implemented

    score = await score_service.get_status(
        user_id=user_id,
        session_id=session_id
    )

    return BaseResponse(
        message="Score succesfully retrieved",
        data={"score": score}
    )
