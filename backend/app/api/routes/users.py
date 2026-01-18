from typing import List
from fastapi import APIRouter, Depends
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=User)
async def create_user(user: User, db: AsyncSession = Depends(get_db)):
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@router.get("/me")
def read_user_me():
    """
    Get current user.
    """
    return {"message": "User me endpoint placeholder"}
