from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

class Score(BaseModel):
    uuid: Optional[UUID] = Field(None, description="Unique identifier for the user")
    challenge_id: Optional[UUID] = Field(None, description="Unique identifier for the challenge")
    user_id: Optional[UUID] = Field(None, description="Unique identifier for the the user")
    session_id: Optional[str] = Field(None, description="Session ID for the user")
    score: Optional[int] = Field(None, description="Score for the challenge")
    is_final: Optional[bool] = Field(False, description="Is the score final")
