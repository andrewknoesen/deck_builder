from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.db import get_db
from app.models.user import User

# OAuth2 scheme
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl="/api/v1/login/access-token",
    auto_error=False
)

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: Optional[str] = Depends(reusable_oauth2)
) -> User:
    """
    Get the current user.
    
    NOTE: This is a SIMPLIFIED implementation for development.
    It returns the first user found in the database if authentication is skipped or fails,
    allowing the frontend to work without a full Google Auth flow (which requires valid tokens).
    
    In a production env, this MUST verify the Google ID token.
    """
    
    # 1. TODO: If token is present, verify it with Google (e.g. google.oauth2.id_token.verify_oauth2_token)
    #    and extract the google_sub. Then find the user by google_sub.
    
    # 2. For now, just return the first user (Dev mode)
    result = await db.execute(select(User))
    user = result.scalars().first()
    
    if not user:
        # If no user exists, create a default dev user
        user = User(
            email="dev@example.com",
            full_name="Dev User", 
            google_sub="dev_sub_12345",
            is_active=True
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
    return user
