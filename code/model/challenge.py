from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum

class ChallengeDifficulty(str, Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"

class ChallengeRequirements(BaseModel):
    min_tokens: int = Field(default=1, description="Minimum tokens required")
    max_tokens: int = Field(default=512, description="Maximum tokens allowed")
    temperature: float = Field(default=0.7, description="Temperature setting")

class Challenge(BaseModel):
    id: str = Field(..., description="Unique identifier for the challenge")
    title: str = Field(..., description="Challenge title")
    description: str = Field(..., description="Detailed description")
    difficulty: ChallengeDifficulty = Field(..., description="Challenge difficulty level")
    points: int = Field(..., description="Points awarded for completion")
    time_limit: Optional[int] = Field(None, description="Optional time limit in seconds")
    requirements: ChallengeRequirements = Field(default_factory=ChallengeRequirements)
    system_prompt: str = Field(..., description="System prompt for the challenge")
    flag: str = Field(..., description="Flag to be retrieved")
    example_prompt: str = Field(..., description="Example of a successful prompt")

class AskRequest(BaseModel):
    """Request model for the ask endpoint."""
    challenge_id: str = Field(..., description="ID of the challenge")
    prompt: str = Field(..., description="User's input prompt")
    user_id: str = Field(..., description="ID of the user")

class ChallengeResponse(BaseModel):
    success: bool = Field(..., description="Whether the response is successful")
    error: Optional[str] = Field(None, description="Error message if any")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")

class ChallengeAttempt(BaseModel):
    challenge_id: str = Field(..., description="ID of the challenge attempted")
    user_id: str = Field(..., description="ID of the user attempting the challenge")
    prompt: str = Field(..., description="Prompt used in the attempt")
    response: str = Field(..., description="LLM response to the attempt")
    success: bool = Field(..., description="Whether the attempt was successful")
    timestamp: str = Field(..., description="Timestamp of the attempt")
