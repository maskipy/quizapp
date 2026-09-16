"""
Deck routes.
"""

from fastapi import APIRouter, status

from app.api.deps import CurrentUser
from app.db.session import SessionDep
from app.models.deck import Deck, DeckCreate, DeckPublic

router = APIRouter(prefix="/decks", tags=["decks"])


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
