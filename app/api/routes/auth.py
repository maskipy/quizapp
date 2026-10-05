"""
Auth routes: registration and login.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlmodel import SQLModel, select

from app.api.deps import CurrentUser
from app.core.security import create_access_token, hash_password_async, verify_password_async
from app.db.session import SessionDep
from app.models.user import User, UserCreate, UserPublic

router = APIRouter(prefix="/auth", tags=["auth"])


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


def email_taken() -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, session: SessionDep) -> User:
    existing = await session.exec(select(User).where(User.email == user_in.email))
    if existing.first() is not None:
        raise email_taken()

    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=await hash_password_async(user_in.password),
    )
    session.add(user)
    try:
        await session.commit()
    except IntegrityError:
        # Two requests registered the same email at the same moment: both passed the
        # check above, and the unique index rejected the second one.
        await session.rollback()
        raise email_taken() from None
    await session.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: SessionDep,
) -> Token:
    # Emails are stored lowercase (see UserCreate); normalise what was typed too --
    # phone keyboards love to capitalise the first letter.
    email = form_data.username.strip().lower()
    result = await session.exec(select(User).where(User.email == email))
    user = result.first()

    if user is None or not await verify_password_async(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return Token(access_token=create_access_token(subject=str(user.id)))


@router.get("/me", response_model=UserPublic)
async def read_current_user(current_user: CurrentUser) -> User:
    return current_user
