from asyncpg import Connection
from fastapi import APIRouter, Depends, Request, status

from core.user_service import UserService
from database import get_connection
from error.exceptions import Hack2mException
from log.logger import get_logger
from model.api.requests import UserRequest
from model.api.responses import BaseResponse
from model.user import User


logger = get_logger("user")
router = APIRouter()


@router.post("/users", response_model=BaseResponse)
async def create_user(
    user: UserRequest,
    db: Connection = Depends(get_connection)) -> BaseResponse:
    """Create a new user.

    Args:
        user (UserRequest): the user data to create.
        db (Connection): the database connection injected by FastAPI.
    Returns:
        BaseResponse: the response containing the created user data.
    Raises:
        Hack2mException: if the user already exists or if there is
        an error during user creation.
    """
    try:
        user_service = UserService(db)
        new_user = await user_service.create_user(user)
        response = User(**new_user.model_dump())
        return BaseResponse(
            message="User created successfully",
            data={"user": response}
        )
    except Hack2mException as e:
        raise e
    except Exception as e:
        logger.exception("Error creating user", exc=e)
        raise Hack2mException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.post("/users/link-account", response_model=BaseResponse)
async def link_session_to_user(
    request: Request,
    user: UserRequest,
    db: Connection = Depends(get_connection)
) -> BaseResponse:
    """Link an anonymous session to a real user.

    Args:
        session_id (str): The session ID to link
        user_id (UUID): The user ID to link to
        db (Connection): Database connection

    Returns:
        BaseResponse: Success message
    """
    try:
        user_service = UserService(db)
        session_id = request.cookies.get("session_id")
        await user_service.link_session_to_user(session_id, user)
        return BaseResponse(
            message="Session linked to user successfully",
            data={}
        )
    except Hack2mException as e:
        raise e
    except Exception as e:
        logger.exception("Error linking session to user", exc=e)
        raise Hack2mException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
