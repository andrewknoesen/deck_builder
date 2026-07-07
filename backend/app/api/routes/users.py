from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.user import User
from app.schemas.user import UserCreate

router = APIRouter()

@router.post("/", response_model=User)
async def create_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    user = User.model_validate(user_in)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@router.get("/me", response_model=User)
async def read_user_me(current_user: User = Depends(get_current_user)):
    """
    Get current user.
    """
    return current_user
