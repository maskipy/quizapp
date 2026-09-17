"""
Deck routes.
"""

from fastapi import APIRouter, Query, status
from sqlalchemy import func
from sqlmodel import SQLModel, select

from app.api.deps import CurrentUser
from app.db.session import SessionDep
from app.models.deck import Deck, DeckCreate, DeckPublic

router = APIRouter(prefix="/decks", tags=["decks"])


class DeckPage(SQLModel):
    items: list[DeckPublic]
    total: int
    limit: int
    offset: int


@router.post("", response_model=DeckPublic, status_code=status.HTTP_201_CREATED)
async def create_deck(
    deck_in: DeckCreate,
    current_user: CurrentUser,
    session: SessionDep,
) -> Deck:
    deck = Deck(**deck_in.model_dump(), owner_id=current_user.id)
    session.add(deck)
    await session.commit()
    await session.refresh(deck)
    return deck


@router.get("", response_model=DeckPage)
async def list_my_decks(
    current_user: CurrentUser,
    session: SessionDep,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> DeckPage:
    total = (
        await session.exec(select(func.count(Deck.id)).where(Deck.owner_id == current_user.id))
    ).one()

    decks = (
        await session.exec(
            select(Deck)
            .where(Deck.owner_id == current_user.id)
            .order_by(Deck.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
    ).all()

    return DeckPage(items=list(decks), total=total, limit=limit, offset=offset)
