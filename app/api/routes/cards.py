"""
Card routes -- nested under a deck.
"""

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, get_owned_deck
from app.db.session import SessionDep
from app.models.deck import Card, CardCreate, CardPublic

router = APIRouter(prefix="/decks/{deck_id}/cards", tags=["cards"])


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
