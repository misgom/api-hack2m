from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config.settings import Settings
from log.logger import setup_logging, logger
from api.routers import challenges, auth
from ai.llm_handler import LLMHandler

# Initialize settings
settings = Settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown events.
    """
    # Setup logging
    setup_logging()
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

# Include routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(challenges.router, prefix=settings.API_V1_STR)