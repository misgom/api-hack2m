from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from model.challenges.challenge import Challenge, ChallengeDifficulty


class BaseResponse(BaseModel):
    success: bool = Field(True, description="Whether the response is successful")
    error: Optional[str] = Field(None, description="Error message if any")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")

class ErrorResponse(BaseModel):
    success: bool = Field(False, description="Whether the response is successful")
    error: str = Field(..., description="Error message")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")

class ChallengeDefinition(BaseModel):
    id: str = Field(..., description="Unique identifier for the challenge")
    title: str = Field(..., description="Challenge title")
    description: str = Field(..., description="Detailed description")
    difficulty: ChallengeDifficulty = Field(..., description="Challenge difficulty level")
    points: int = Field(..., description="Points awarded for completion")

class ChallengeDefinitionsResponse(BaseModel):
    challenges: list[Challenge] = Field(..., description="List of challenge definitions")

class UserResponse(BaseModel):
    name: Optional[str] = Field(..., description="Name of the user")
    email: Optional[str] = Field(..., description="Email address of the user")
    session_id: Optional[str] = Field(..., description="Session ID for the user")
