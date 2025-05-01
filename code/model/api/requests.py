from fastapi import Form, UploadFile
from pydantic import BaseModel, Field
from typing import Optional


class AskRequest(BaseModel):
    """Request model for the ask endpoint."""
    challenge_id: str = Form(..., description="ID of the challenge")
    prompt: str = Form(..., description="User's input prompt")
    file: Optional[UploadFile] = Form(None, description="File to be uploaded")

class VerifyRequest(BaseModel):
    """Request model for the verify endpoint."""
    challenge_id: str = Field(..., description="ID of the challenge")
    flag: str = Field(..., description="Flag to be verified")

class UserRequest(BaseModel):
    """Request model for the user endpoint."""
    name: str = Field(..., description="Username of the user")
    email: str = Field(..., description="Email address of the user")
    password: str = Field(..., description="Password of the user")
