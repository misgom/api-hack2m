from fastapi import HTTPException, status
from typing import Optional

class Hack2mException(Exception):
    """Base exception for Hack2m application."""
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.status_code = status_code
        super().__init__(message)

class ChallengeNotFoundError(Hack2mException):
    """Exception raised when a challenge is not found."""
    def __init__(self, challenge_id: str):
        super().__init__(
            f"Challenge with ID {challenge_id} not found",
            status.HTTP_404_NOT_FOUND
        )

class InvalidFlagError(Hack2mException):
    """Exception raised when an invalid flag is submitted."""
    def __init__(self, message: str = "Invalid flag format"):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)

class RateLimitExceededError(Hack2mException):
    """Exception raised when rate limit is exceeded."""
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status.HTTP_429_TOO_MANY_REQUESTS)

class LLMError(Hack2mException):
    """Exception raised when there's an error with the LLM."""
    def __init__(self, message: str = "Error with LLM service"):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR)

class AuthenticationError(Hack2mException):
    """Exception raised when there's an authentication error."""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)

class AuthorizationError(Hack2mException):
    """Exception raised when there's an authorization error."""
    def __init__(self, message: str = "Not authorized"):
        super().__init__(message, status.HTTP_403_FORBIDDEN)

def handle_exception(e: Exception) -> HTTPException:
    """
    Handle exceptions and convert them to HTTP exceptions.

    Args:
        e: Exception to handle

    Returns:
        HTTPException with appropriate status code and message
    """
    if isinstance(e, Hack2mException):
        return HTTPException(
            status_code=e.status_code,
            detail=e.message
        )
    else:
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
