from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "MTG Deck Builder"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "sqlite:///./sql_app.db" # Default to local sqlite
    
    # Security
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    SECRET_KEY: str = "changethis" # TODO: Change in production
    
    # External APIs
    SCRYFALL_BASE_URL: str = "https://api.scryfall.com"

    class Config:
        env_file = ".env"

settings = Settings()
