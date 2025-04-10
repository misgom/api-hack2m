from pydantic_settings import BaseSettings
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Hack2m CTF Platform"

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "secret-key")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"

    # CORS
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "*").split(",")

    # LLM Settings
    LLM_FOLDER: str = os.getenv("OLLAMA_MODELS", "C:/AI Models")
    LLM_MODEL: str = f"{LLM_FOLDER}/Llama-3.2-3B-Instruct-uncensored"
    LLM_QUANTIZATION: bool = os.getenv("LLM_QUANTIZATION", False)
    LLM_LOAD_IN_8BIT: bool = os.getenv("LLM_LOAD_IN_8BIT", False)
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 512
    LLM_CONTEXT_WINDOW: int = 2048

    # Challenge Settings
    CHALLENGE_TIMEOUT: int = 300  # seconds
    MAX_ATTEMPTS_PER_CHALLENGE: int = 10

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100

    class Config:
        case_sensitive = True
        env_file = ".env"
