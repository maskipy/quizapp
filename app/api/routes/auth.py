"""
Auth routes: registration
"""

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.core.security import hash_password
from app.db.session import SessionDep
from app.models.user import User, UserCreate, UserPublic

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, session: SessionDep) -> User:
    existing = await session.exec(select(User).where(User.email == user_in.email))
    if existing.first() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=hash_password(user_in.password),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
