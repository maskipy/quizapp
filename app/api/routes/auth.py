"""
Auth routes: registration and login.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import SQLModel, select

from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import SessionDep
from app.models.user import User, UserCreate, UserPublic

router = APIRouter(prefix="/auth", tags=["auth"])


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


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


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: SessionDep,
) -> Token:
    # OAuth2PasswordRequestForm names the field "username" per the OAuth2 spec --
    # we just treat whatever's typed in there as the email.
    result = await session.exec(select(User).where(User.email == form_data.username))
    user = result.first()

    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=str(user.id))
    return Token(access_token=access_token)
