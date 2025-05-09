from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from uuid import uuid4

from ai.llm_handler import LLMHandler
from api.routers import challenges, auth, users, scores
from config.settings import settings
from database import connect_to_db, disconnect_from_db
from log.logger import get_logger
from error.exceptions import Hack2mException
from error.handlers import (
    hack2m_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)


# Get logger instance
logger = get_logger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application resources on startup and shutdown events.
    """
    await connect_to_db(app)
    # Initialize LLM handler (singleton)
    LLMHandler(settings)

    yield
    await disconnect_from_db(app)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="LLM Hacking CTF Platform API",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def auth_middleware(
    request: Request,
    call_next
) -> Request:
    """
    Middleware to handle anonymous authentication
    """
    session_id = request.cookies.get("session_id")
    if not session_id and request.method != "OPTIONS":
        logger.info(f"URL: {request.url} - No session_id found in cookies")
        session_id = str(uuid4())
        response = await call_next(request)
        response.set_cookie(
            key="session_id",
            value=session_id,
            path="/",
            httponly=True,
            secure=settings.SESSION_COOKIE_SECURITY,
            samesite="None" if settings.SESSION_COOKIE_SECURITY else "Lax",
        )
        return response

    response = await call_next(request)
    return response

# Register custom exception handlers
@app.exception_handler(HTTPException)
async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    return await http_exception_handler(request, exc)

@app.exception_handler(Hack2mException)
async def handle_hack2m_exception(request: Request, exc: Hack2mException) -> JSONResponse:
    return await hack2m_exception_handler(request, exc)

@app.exception_handler(RequestValidationError)
async def handle_validation_exception(request: Request, exc: RequestValidationError) -> JSONResponse:
    return await validation_exception_handler(request, exc)

@app.exception_handler(Exception)
async def handle_general_exception(request: Request, exc: Exception) -> JSONResponse:
    return await general_exception_handler(request, exc)

# Include routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(challenges.router, prefix=settings.API_V1_STR)
app.include_router(users.router, prefix=settings.API_V1_STR)
app.include_router(scores.router, prefix=settings.API_V1_STR)
