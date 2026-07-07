from typing import Optional
from pydantic import BaseModel

class UserCreate(BaseModel):
    email: str
    full_name: Optional[str] = None
    google_sub: str
