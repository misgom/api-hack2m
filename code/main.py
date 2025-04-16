from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError, HTTPException
from contextlib import asynccontextmanager
from config.settings import settings
from log.logger import get_logger
from api.routers import challenges, auth
from ai.llm_handler import LLMHandler
from error.handlers import (
    hack2m_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from error.exceptions import Hack2mException
from fastapi.responses import JSONResponse

# Get logger instance
logger = get_logger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown events.
    """
    logger.info("Starting up application...")

    # Initialize LLM handler (singleton)
    LLMHandler(settings)

    yield

    # Cleanup
    logger.info("Shutting down application...")
    # The singleton will handle its own cleanup

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