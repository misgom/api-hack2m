"""
Models package for Hack2m CTF Platform.

Contains all data models and schemas.
"""

from .challenges.challenge import (
    Challenge,
    ChallengeAttempt,
    ChallengeDifficulty
)

from .api.requests import (
    AskRequest,
    VerifyRequest
)

from .api.responses import (
    BaseResponse,
    ChallengeDefinitionsResponse
)
