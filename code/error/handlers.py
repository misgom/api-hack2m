from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from .exceptions import Hack2mException

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Custom exception handler for HTTP exceptions.
    Returns responses following the standard error template.
    """
    return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": exc.__class__.__name__,
                "message": str(exc.detail),
                "data": {}
            }
        )

async def hack2m_exception_handler(request: Request, exc: Hack2mException) -> JSONResponse:
    """
    Custom exception handler for Hack2m exceptions.
    Returns responses following the standard error template.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.__class__.__name__,
            "message": str(exc),
            "data": {}
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Custom exception handler for validation errors.
    Returns responses following the standard error template.
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "ValidationError",
            "message": "Invalid request data",
            "data": {
                "details": exc.errors()
            }
        }
    )

async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Custom exception handler for unhandled exceptions.
    Returns responses following the standard error template.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "data": {}
        }
    )
