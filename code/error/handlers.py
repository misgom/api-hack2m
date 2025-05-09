from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.responses import JSONResponse

from .exceptions import Hack2mException
from model.api.responses import ErrorResponse


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Custom exception handler for HTTP exceptions.
    Returns responses following the standard error template.
    """
    return JSONResponse(
            status_code=exc.status_code,
            content=jsonable_encoder(ErrorResponse(
                error=exc.__class__.__name__,
                message=str(exc.detail)
            ))
    )

async def hack2m_exception_handler(request: Request, exc: Hack2mException) -> JSONResponse:
    """
    Custom exception handler for Hack2m exceptions.
    Returns responses following the standard error template.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(ErrorResponse(
            error=exc.__class__.__name__,
            message=str(exc)
        ))
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Custom exception handler for validation errors.
    Returns responses following the standard error template.
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder(ErrorResponse(
            error="ValidationError",
            message="Invalid request data",
            data={
                "details": exc.errors()
            }
        ))
    )

async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Custom exception handler for unhandled exceptions.
    Returns responses following the standard error template.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=jsonable_encoder(ErrorResponse(
            error="InternalServerError",
            message="An unexpected error occurred"
        ))
    )
