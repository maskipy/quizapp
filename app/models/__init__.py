"""
Importing every model here guarantees SQLAlchemy can resolve the string forward
references between them (e.g. User.decks -> "Deck"), and that Alembic sees every table.
"""

from app.models.classroom import (
    ClassDeck,
    ClassMembership,
    Classroom,
    ClassroomBase,
    ClassroomCreate,
    ClassroomPublic,
    DeckShare,
    JoinRequest,
    MemberPage,
    MemberPublic,
    SharedDeckPage,
    SharedDeckPublic,
)
from app.models.deck import (
    Card,
    CardBase,
    CardCreate,
    CardPublic,
    CardUpdate,
    Deck,
    DeckBase,
    DeckCreate,
    DeckPublic,
    DeckUpdate,
)
from app.models.user import User, UserBase, UserCreate, UserPublic

__all__ = [
    "Card",
    "CardBase",
    "CardCreate",
    "CardPublic",
    "CardUpdate",
    "ClassDeck",
    "ClassMembership",
    "Classroom",
    "ClassroomBase",
    "ClassroomCreate",
    "ClassroomPublic",
    "Deck",
    "DeckBase",
    "DeckCreate",
    "DeckPublic",
    "DeckShare",
    "DeckUpdate",
    "JoinRequest",
    "MemberPage",
    "MemberPublic",
    "SharedDeckPage",
    "SharedDeckPublic",
    "User",
    "UserBase",
    "UserCreate",
    "UserPublic",
]
