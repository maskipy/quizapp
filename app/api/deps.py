"""
Shared FastAPI dependencies used across routers.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import selectinload
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.security import decode_access_token
from app.db.session import SessionDep
from app.models.deck import Deck
from app.models.user import User

# tokenUrl points Swagger's "Authorize" button at our real login endpoint.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    session: SessionDep,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    subject = decode_access_token(token)
    if subject is None:
        raise credentials_exception

    try:
        user_id = int(subject)
    except ValueError:
        raise credentials_exception from None

    user = await session.get(User, user_id)
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_owned_deck(
    deck_id: int,
    current_user: User,
    session: AsyncSession,
    *,
    with_cards: bool = False,
) -> Deck:
    """
    Fetch a deck the current user actually owns, or 404.

    with_cards controls whether Deck.cards gets eager-loaded via
    selectinload. Since the relationship is lazy="raise", any endpoint that
    needs deck.cards MUST pass with_cards=True, or reading that attribute
    later raises instead of silently querying.
    """
    options = [selectinload(Deck.cards)] if with_cards else []
    deck = await session.get(Deck, deck_id, options=options)
    if deck is None or deck.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deck not found")
    return deck
