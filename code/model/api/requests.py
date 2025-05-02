from fastapi import Form, UploadFile
from pydantic import BaseModel, Field
from typing import Optional


class AskRequest(BaseModel):
    """Request model for the ask endpoint."""
    challenge_id: Optional[str] = Form(None, description="ID of the challenge")
    prompt: Optional[str] = Form(None, description="User's input prompt")
    file: Optional[UploadFile] = Form(None, description="File to be uploaded")

class VerifyRequest(BaseModel):
    """Request model for the verify endpoint."""
    challenge_id: str = Field(..., description="ID of the challenge")
    flag: str = Field(..., description="Flag to be verified")

class UserRequest(BaseModel):
    """Request model for the user endpoint."""
    name: Optional[str] = Field(None, description="Username of the user")
    email: Optional[str] = Field(None, description="Email address of the user")
    password: Optional[str] = Field(None, description="Password of the user")
    session_id: Optional[str] = Field(None, description="Session ID of the user")
