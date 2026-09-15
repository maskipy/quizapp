"""
Deck and Card models -- a Deck (a quiz/flashcard set) belongs to a User and
contains many Cards (question/answer pairs).

Relationships default to lazy="raise": accessing e.g. deck.cards without
having explicitly eager-loaded it (via selectinload() in the query) raises
immediately, instead of attempting a lazy load -- which wouldn't work under
an async engine anyway (it fails with MissingGreenlet, since a lazy load is
a blocking-style DB call and there's no way to await it from inside a plain
attribute access). This forces every place that needs related data to say
so explicitly in its query, rather than triggering a surprise query (or a
crash) from something that looks like a harmless attribute read.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from app.models.user import utcnow

if TYPE_CHECKING:
    from app.models.user import User


class DeckBase(SQLModel):
    title: str
    description: str | None = None


class Deck(DeckBase, table=True):
    __tablename__ = "decks"

    id: int | None = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=utcnow)

    owner: "User" = Relationship(back_populates="decks", sa_relationship_kwargs={"lazy": "raise"})
    cards: list["Card"] = Relationship(
        back_populates="deck",
        sa_relationship_kwargs={"lazy": "raise", "cascade": "all, delete-orphan"},
    )


class DeckCreate(DeckBase):
    pass


class DeckPublic(DeckBase):
    id: int
    owner_id: int
    created_at: datetime


class CardBase(SQLModel):
    question: str
    answer: str


class Card(CardBase, table=True):
    __tablename__ = "cards"

    id: int | None = Field(default=None, primary_key=True)
    deck_id: int = Field(foreign_key="decks.id", index=True)
    created_at: datetime = Field(default_factory=utcnow)

    deck: Deck = Relationship(back_populates="cards", sa_relationship_kwargs={"lazy": "raise"})


class CardCreate(CardBase):
    pass


class CardPublic(CardBase):
    id: int
    deck_id: int
    created_at: datetime
