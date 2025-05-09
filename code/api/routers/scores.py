from asyncpg import Connection
from fastapi import APIRouter, Depends

from core.score_service import ScoreService
from database import get_connection

from api.routers.auth import get_current_user
from log.logger import get_logger
from model.api.responses import BaseResponse
from model.user import User


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
    current_user: User = Depends(get_current_user),
    db: Connection = Depends(get_connection)
) -> BaseResponse:
    """Get score endpoint

    Args:
        current_user (User, optional): the current user. Defaults to Depends(get_current_user).
        db (Connection, optional): the db connection. Defaults to Depends(get_connection).

    Raises:
        Hack2mException: if the challenge is not found

    Returns:
        BaseResponse: the response with the score
    """
    score_service = ScoreService(db)

    score = await score_service.get_status(
        user_id=current_user.uuid,
        session_id=current_user.session_id
    )

    return BaseResponse(
        message="Score succesfully retrieved",
        data={"score": score}
    )
