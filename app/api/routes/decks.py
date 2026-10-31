"""
Deck routes.
"""

from fastapi import APIRouter, Query, status
from sqlalchemy import func
from sqlmodel import SQLModel, select

from app.api.deps import CurrentUser, get_owned_deck, get_readable_deck
from app.db.session import SessionDep
from app.models.classroom import ClassDeck, Classroom, DeckShare
from app.models.deck import CardPublic, Deck, DeckCreate, DeckPublic, DeckUpdate

router = APIRouter(prefix="/decks", tags=["decks"])


class DeckPage(SQLModel):
    items: list[DeckPublic]
    total: int
    limit: int
    offset: int


class DeckWithCards(DeckPublic):
    cards: list[CardPublic]


@router.post("", response_model=DeckPublic, status_code=status.HTTP_201_CREATED)
async def create_deck(deck_in: DeckCreate, current_user: CurrentUser, session: SessionDep) -> Deck:
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
            # id is the tie-breaker: without it, two decks with the same timestamp can
            # swap places between requests, so a deck could repeat or vanish across pages.
            .order_by(Deck.created_at.desc(), Deck.id.desc())
            .offset(offset)
            .limit(limit)
        )
    ).all()
    return DeckPage(items=list(decks), total=total, limit=limit, offset=offset)


@router.get("/{deck_id}", response_model=DeckWithCards)
async def get_deck(deck_id: int, current_user: CurrentUser, session: SessionDep) -> Deck:
    # Reading: the owner, or a member of a class this deck is shared with.
    return await get_readable_deck(deck_id, current_user, session, with_cards=True)


@router.get("/{deck_id}/classes", response_model=list[DeckShare])
async def list_deck_shares(
    deck_id: int, current_user: CurrentUser, session: SessionDep
) -> list[DeckShare]:
    """Which classes this deck is shared with. Owner only."""
    await get_owned_deck(deck_id, current_user, session)
    rows = (
        await session.exec(
            select(Classroom.id, Classroom.name, ClassDeck.shared_at)
            .join(ClassDeck, ClassDeck.class_id == Classroom.id)
            .where(ClassDeck.deck_id == deck_id)
            .order_by(ClassDeck.shared_at.desc(), Classroom.id.desc())
        )
    ).all()
    return [DeckShare(class_id=cid, name=name, shared_at=at) for cid, name, at in rows]


@router.patch("/{deck_id}", response_model=DeckPublic)
async def update_deck(
    deck_id: int,
    deck_in: DeckUpdate,
    current_user: CurrentUser,
    session: SessionDep,
) -> Deck:
    deck = await get_owned_deck(deck_id, current_user, session)
    for key, value in deck_in.model_dump(exclude_unset=True).items():
        setattr(deck, key, value)
    session.add(deck)
    await session.commit()
    await session.refresh(deck)
    return deck


@router.delete("/{deck_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deck(deck_id: int, current_user: CurrentUser, session: SessionDep) -> None:
    deck = await get_owned_deck(deck_id, current_user, session)
    await session.delete(deck)
    await session.commit()
