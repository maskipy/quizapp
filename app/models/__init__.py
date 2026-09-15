"""
Importing every model here guarantees SQLAlchemy can resolve the string
forward references between them (e.g. User.decks -> "Deck"). Without this,
importing only app.models.user leaves "Deck" unregistered and any query
against User fails at mapper-configuration time.

Alembic's env.py relies on this too -- it imports this package rather than
each model file individually.
"""

from app.models.deck import (
    Card,
    CardBase,
    CardCreate,
    CardPublic,
    Deck,
    DeckBase,
    DeckCreate,
    DeckPublic,
)
from app.models.user import User, UserBase, UserCreate, UserPublic

__all__ = [
    "Card",
    "CardBase",
    "CardCreate",
    "CardPublic",
    "Deck",
    "DeckBase",
    "DeckCreate",
    "DeckPublic",
    "User",
    "UserBase",
    "UserCreate",
    "UserPublic",
]
