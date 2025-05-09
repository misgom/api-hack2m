from asyncpg import Connection
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from api.routers.auth import get_current_user, create_access_token
from core.user_service import UserService
from database import get_connection
from error.exceptions import Hack2mException
from log.logger import get_logger
from model.api.requests import UserRequest
from model.api.responses import BaseResponse, UserResponse
from model.user import User


logger = get_logger("user")
router = APIRouter()


@router.get("/user", response_model=BaseResponse)
async def get_user(current_user: User = Depends(get_current_user)) -> BaseResponse:
    """Get the current user

    Args:
        request (Request): the request
        db (Connection): the database connection injected by FastAPI

    Returns:
        BaseResponse: the base Response with the current user object
    """
    try:
        return BaseResponse(
            message="Current user retrieved",
            data={"user": UserResponse(current_user)}
        )
    except Hack2mException as h2m_exc:
        raise h2m_exc
    except Exception as e:
        logger.exception("Error retrieving current user", exc=e)
        raise e

@router.post("/users/link-account", response_model=BaseResponse)
async def link_session_to_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    current_user: User = Depends(get_current_user),
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
        await user_service.link_session_to_user(current_user.session_id, form_data.username, form_data.password)
        token = create_access_token(data={"sub": form_data.username, "is_anonymous": False})
        return BaseResponse(
            message="Session linked to user successfully",
            data={"access_token": token, "token_type": "bearer"}
        )
    except Hack2mException as e:
        raise e
    except Exception as e:
        logger.exception("Error linking session to user", exc=e)
        raise Hack2mException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
