"""
Card routes -- nested under a deck. A card can't exist without a deck, so
every operation here has to prove the requesting user actually owns that
deck first.
"""

from fastapi import APIRouter, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import CurrentUser
from app.db.session import SessionDep
from app.models.deck import Card, CardCreate, CardPublic, Deck
from app.models.user import User

router = APIRouter(prefix="/decks/{deck_id}/cards", tags=["cards"])


async def _get_owned_deck(deck_id: int, current_user: User, session: AsyncSession) -> Deck:
    """
    Fetch a deck the current user actually owns, or 404.
    """
    deck = await session.get(Deck, deck_id)
    if deck is None or deck.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deck not found")
    return deck


@router.post("", response_model=CardPublic, status_code=status.HTTP_201_CREATED)
async def add_card(
    deck_id: int,
    card_in: CardCreate,
    current_user: CurrentUser,
    session: SessionDep,
) -> Card:
    await _get_owned_deck(deck_id, current_user, session)

    card = Card(**card_in.model_dump(), deck_id=deck_id)
    session.add(card)
    await session.commit()
    await session.refresh(card)
    return card
