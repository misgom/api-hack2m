from asyncpg import Connection
from datetime import datetime
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel
from typing import Optional
from uuid import uuid4


from config.settings import settings
from core.user_service import UserService
from database import get_connection
from log.logger import get_logger
from model.api.responses import BaseResponse
from model.api.requests import UserRequest
from model.user import User


router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
logger = get_logger("auth")

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

def create_access_token(data: dict) -> str:
    """
    Create a JWT access token.

    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    expire = int(datetime.now().timestamp()) + settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Connection = Depends(get_connection)
) -> User:
    """
    Get the current user from the JWT token.

    Args:
        token: JWT token

    Returns:
        User ID

    Raises:
        HTTPException: If token is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError as jwt_error:
        logger.error(f"JWT token is invalid: {jwt_error}")
        raise credentials_exception

    user_service = UserService(db)
    user = await user_service.find_user_by_name(username)
    logger.info(f"User {user} found in database")
    if not user:
        raise credentials_exception
    return user

@router.post("/token", response_model=Token)
async def login_anonymous(
    request: Request,
    db: Connection = Depends(get_connection)
) -> Token:
    """Login endpoint to get access token for anonymous users.

    Args:
        db (Connection, optional): The db connection. Defaults to Depends(get_connection).

    Raises:
        HTTPException: Exception raised if the user is not found or if the token is invalid.

    Returns:
        Token: the access token for the user.
    """
    user_service = UserService(db)
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = str(uuid4())
        user = UserRequest(
            name=f"anon-{session_id[:8]}",
            session_id=session_id
        )
        logger.info(f"Creating {user.name} for request {request.method} {request.url}")
        anon_user = await user_service.create_anonymous_user(user)
    else:
        anon_user = await user_service.find_user_by_session_id(session_id=session_id)
        if not anon_user:
            user = UserRequest(
                name=f"anon-{session_id[:8]}",
                session_id=session_id
            )
            anon_user = await user_service.create_anonymous_user(user)
    token = create_access_token(data={"sub": anon_user.name, "is_anonymous": True})
    return Token(access_token=token, token_type="bearer")

@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Connection = Depends(get_connection)
) -> Token:
    """
    Login endpoint to get access token.

    Args:
        form_data: Username and password

    Returns:
        JWT access token

    Raises:
        HTTPException: If credentials are invalid
    """
    user_service = UserService(db)
    user = await user_service.authenticate_user(
        name=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.name, "is_anonymous": False})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=BaseResponse)
async def register_user(
    request: Request,
    name: str = Form(..., description="Username"),
    email: str = Form(..., description="User email"),
    password: str = Form(..., description="User password"),
    db: Connection = Depends(get_connection)
) -> BaseResponse:
    """
    Register a new user.

    Args:
        name: Username
        email: User email
        password: User password

    Returns:
        BaseResponse: Response object

    Raises:
        HTTPException: If user already exists or registration fails
    """
    user_service = UserService(db)
    try:
        await user_service.create_user(
            name=name,
            email=email,
            password=password,
            session_id=request.cookies.get("session_id")
        )
        return BaseResponse(message="User registered successfully")
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
