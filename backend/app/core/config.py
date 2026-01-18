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

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
