from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "MTG Deck Builder"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/deck_builder"
    )

    # Security
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    SECRET_KEY: str = "changethis" # TODO: Change in production
    
    # External APIs
    SCRYFALL_BASE_URL: str = "https://api.scryfall.com"

    # AI Configuration
    HF_TOKEN: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    GOOGLE_PROJECT_ID: Optional[str] = None
    GOOGLE_LOCATION: str = "us-central1"
    AI_MODEL_NAME: str = "gemini-2.5-flash"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
