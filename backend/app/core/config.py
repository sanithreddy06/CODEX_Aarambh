import os
from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import field_validator

class Settings(BaseSettings):
    APP_NAME: str = "CODEX"
    APP_ENV: str = "development"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]
    
    DATABASE_URL: str = "sqlite+aiosqlite:///./codex.db"
    
    STORAGE_DIR: str = "./data/storage"
    PROJECTS_DIR: str = "./data/projects"
    MAX_UPLOAD_SIZE_MB: int = 50
    MAX_UNCOMPRESSED_SIZE_MB: int = 250
    
    AI_PROVIDER: str = "gemini" # gemini, groq, openai, local, deterministic
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    LOCAL_MODEL_URL: str = "http://localhost:11434/v1"
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        return ["*"]

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

os.makedirs(settings.STORAGE_DIR, exist_ok=True)
os.makedirs(settings.PROJECTS_DIR, exist_ok=True)
