"""
Card routes -- nested under a deck.
"""

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import CurrentUser, get_owned_deck
from app.db.session import SessionDep
from app.models.deck import Card, CardCreate, CardPublic
from app.models.user import User

router = APIRouter(prefix="/decks/{deck_id}/cards", tags=["cards"])


class CardPage(SQLModel):
    items: list[CardPublic]
    total: int
    limit: int
    offset: int


class CardUpdate(SQLModel):
    question: str | None = None
    answer: str | None = None


async def get_owned_card(
    deck_id: int, card_id: int, current_user: User, session: AsyncSession
) -> Card:
    """
    confirm the deck belongs to this user first, then confirm the card
    actually belongs to *that* deck.
    """
    await get_owned_deck(deck_id, current_user, session)
    card = await session.get(Card, card_id)
    if card is None or card.deck_id != deck_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
    return card


@router.post("", response_model=CardPublic, status_code=status.HTTP_201_CREATED)
async def add_card(
    deck_id: int,
    card_in: CardCreate,
    current_user: CurrentUser,
    session: SessionDep,
) -> Card:
    await get_owned_deck(deck_id, current_user, session)

    card = Card(**card_in.model_dump(), deck_id=deck_id)
    session.add(card)
    await session.commit()
    await session.refresh(card)
    return card


@router.get("", response_model=CardPage)
async def list_cards(
    deck_id: int,
    current_user: CurrentUser,
    session: SessionDep,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> CardPage:
    await get_owned_deck(deck_id, current_user, session)

    total = (await session.exec(select(func.count(Card.id)).where(Card.deck_id == deck_id))).one()
    cards = (
        await session.exec(
            select(Card)
            .where(Card.deck_id == deck_id)
            .order_by(Card.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
    ).all()
    return CardPage(items=list(cards), total=total, limit=limit, offset=offset)


@router.patch("/{card_id}", response_model=CardPublic)
async def update_card(
    deck_id: int,
    card_id: int,
    card_in: CardUpdate,
    current_user: CurrentUser,
    session: SessionDep,
) -> Card:
    card = await get_owned_card(deck_id, card_id, current_user, session)
    for key, value in card_in.model_dump(exclude_unset=True).items():
        setattr(card, key, value)
    session.add(card)
    await session.commit()
    await session.refresh(card)
    return card


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_card(
    deck_id: int,
    card_id: int,
    current_user: CurrentUser,
    session: SessionDep,
) -> None:
    card = await get_owned_card(deck_id, card_id, current_user, session)
    await session.delete(card)
    await session.commit()
