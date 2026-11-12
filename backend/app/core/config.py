import os
import json
from pathlib import Path
from typing import List, Union, Dict, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "CODEX"
    APP_ENV: str = "development"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]
    LOCAL_ONLY: bool = True
    
    DATABASE_URL: str = "sqlite+aiosqlite:///./codex.db"
    
    STORAGE_DIR: str = "./data/storage"
    PROJECTS_DIR: str = "./data/projects"
    MAX_UPLOAD_SIZE_MB: int = 200
    MAX_UNCOMPRESSED_SIZE_MB: int = 1000
    
    AI_PROVIDER: str = "deterministic"  # deterministic, gemini, groq, openai, local
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

settings = Settings()

os.makedirs(settings.STORAGE_DIR, exist_ok=True)
os.makedirs(settings.PROJECTS_DIR, exist_ok=True)

SETTINGS_FILE = Path(settings.STORAGE_DIR) / "settings.json"

def load_persisted_settings():
    """Loads runtime overrides persisted by the user via Settings page."""
    if SETTINGS_FILE.is_file():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "AI_PROVIDER" in data:
                    settings.AI_PROVIDER = data["AI_PROVIDER"]
                if "GEMINI_API_KEY" in data and data["GEMINI_API_KEY"]:
                    settings.GEMINI_API_KEY = data["GEMINI_API_KEY"]
                if "GROQ_API_KEY" in data and data["GROQ_API_KEY"]:
                    settings.GROQ_API_KEY = data["GROQ_API_KEY"]
                if "OPENAI_API_KEY" in data and data["OPENAI_API_KEY"]:
                    settings.OPENAI_API_KEY = data["OPENAI_API_KEY"]
                if "OPENAI_BASE_URL" in data and data["OPENAI_BASE_URL"]:
                    settings.OPENAI_BASE_URL = data["OPENAI_BASE_URL"]
                if "LOCAL_MODEL_URL" in data and data["LOCAL_MODEL_URL"]:
                    settings.LOCAL_MODEL_URL = data["LOCAL_MODEL_URL"]
                if "MAX_UPLOAD_SIZE_MB" in data and isinstance(data["MAX_UPLOAD_SIZE_MB"], int):
                    settings.MAX_UPLOAD_SIZE_MB = data["MAX_UPLOAD_SIZE_MB"]
                if "MAX_UNCOMPRESSED_SIZE_MB" in data and isinstance(data["MAX_UNCOMPRESSED_SIZE_MB"], int):
                    settings.MAX_UNCOMPRESSED_SIZE_MB = data["MAX_UNCOMPRESSED_SIZE_MB"]
        except Exception:
            pass

def save_persisted_settings(updates: Dict[str, Any]):
    """Persists updated runtime settings to data/storage/settings.json safely."""
    current = {}
    if SETTINGS_FILE.is_file():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                current = json.load(f)
        except Exception:
            current = {}

    for k, v in updates.items():
        if v is not None:
            current[k] = v

    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2)

# Load existing overrides on initialization
load_persisted_settings()
