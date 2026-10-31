"""
Shared FastAPI dependencies used across routers.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.security import decode_access_token
from app.db.session import SessionDep
from app.models.classroom import ClassDeck, ClassMembership
from app.models.deck import Deck
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    session: SessionDep, token: Annotated[str, Depends(oauth2_scheme)]
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


def require_teacher(current_user: CurrentUser) -> User:
    """403, not 404: the endpoint exists and you are logged in; you just lack the role.
    (404 is for hiding that a *resource* exists; this hides nothing.)"""
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Teacher account required"
        )
    return current_user


TeacherUser = Annotated[User, Depends(require_teacher)]


async def get_owned_deck(
    deck_id: int,
    current_user: User,
    session: AsyncSession,
    *,
    with_cards: bool = False,
) -> Deck:
    """Fetch a deck the current user actually owns, or 404.

    Deliberately 404, not 403: a 403 would let a caller tell "this deck doesn't exist"
    apart from "this deck exists but isn't yours", leaking which ids are in use.

    with_cards controls whether Deck.cards gets eager-loaded. Since the relationship is
    lazy="raise", any endpoint that reads deck.cards MUST pass with_cards=True.
    """
    options = [selectinload(Deck.cards)] if with_cards else []
    deck = await session.get(Deck, deck_id, options=options)
    if deck is None or deck.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deck not found")
    return deck


async def get_readable_deck(
    deck_id: int,
    current_user: User,
    session: AsyncSession,
    *,
    with_cards: bool = False,
) -> Deck:
    """Fetch a deck the current user may READ, or 404.

    Readable means: you own it, or it is shared with a class you belong to. This is the
    single place that rule lives. Every endpoint that only reads uses this; every
    endpoint that changes anything keeps using get_owned_deck, so students can never
    edit what they can study.
    """
    options = [selectinload(Deck.cards)] if with_cards else []
    deck = await session.get(Deck, deck_id, options=options)
    if deck is not None and deck.owner_id != current_user.id:
        shared_with_me = (
            await session.exec(
                select(ClassDeck.deck_id)
                .join(ClassMembership, ClassMembership.class_id == ClassDeck.class_id)
                .where(ClassDeck.deck_id == deck_id, ClassMembership.user_id == current_user.id)
                .limit(1)
            )
        ).first()
        if shared_with_me is None:
            deck = None
    if deck is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deck not found")
    return deck
