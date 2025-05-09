import asyncpg
from fastapi import FastAPI, Request, Depends
from typing import AsyncGenerator
from config.settings import settings
from log.logger import get_logger

logger = get_logger("db")

async def connect_to_db(app: FastAPI):
    """Connect to the database using asyncpg and store the connection pool in the app state.

    Args:
        app (FastAPI): the FastAPI application instance.
    """
    logger.info("Connecting to the database...")
    try:
        app.state.pool = await asyncpg.create_pool(settings.DB_URL, min_size=1, max_size=10)
        logger.info("Connected to the database successfully.")
    except Exception as e:
        logger.error(f"Failed to connect to the database: {e}")
        raise

async def disconnect_from_db(app: FastAPI):
    """Disconnect from the database and close the connection pool.

    Args:
        app (FastAPI): the FastAPI application instance.
    """
    logger.info("Disconnecting from the database...")
    try:
        await app.state.pool.close()
        logger.info("Disconnected from the database successfully.")
    except Exception as e:
        logger.error(f"Failed to disconnect from the database: {e}")
        raise

async def get_pool(app: FastAPI) -> asyncpg.pool.Pool:
    """Get the database connection pool from the app state.

    Args:
        app (FastAPI): the FastAPI application instance.

    Returns:
        asyncpg.pool.Pool: the database connection pool.
    """
    return app.state.pool

async def get_connection(
        request: Request
) -> AsyncGenerator[asyncpg.Connection, None]:
    """Get a database connection from the pool.
    This function is used as a dependency in FastAPI routes to provide
    a database connection.

    Args:
        request (Request): the FastAPI request object.
        This is used to access the app state and get the
        connection pool.

    Returns:
        AsyncGenerator[asyncpg.Connection, None]: the database
        connection.
        This connection should be used within an async context manager
        to ensure it is released back to the pool after use.

    Yields:
        Iterator[AsyncGenerator[asyncpg.Connection, None]]: the database
        connection.
    """
    pool = await get_pool(request.app)
    async with pool.acquire() as conn:
        yield conn
