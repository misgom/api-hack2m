from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

class User(BaseModel):
    uuid: UUID = Field(..., description="Unique identifier for the user")
    name: Optional[str] = Field(..., description="Name of the user")
    email: Optional[str] = Field(..., description="Email address of the user")
    session_id: Optional[str] = Field(..., description="Session ID for the user")
