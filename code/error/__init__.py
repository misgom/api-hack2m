"""
Error handling package for Hack2m CTF Platform.

Contains custom exceptions and error handling utilities.
"""

from .exceptions import (
    Hack2mException,
    ChallengeNotFoundError,
    InvalidFlagError,
    RateLimitExceededError,
    LLMError,
    AuthenticationError,
    AuthorizationError,
    handle_exception
) 