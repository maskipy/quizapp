"""
Deck and Card models -- a Deck belongs to a User and contains many Cards.

Relationships use lazy="raise": reading deck.cards without having eager-loaded it
(selectinload) raises immediately, because a lazy load can't be awaited under an
async engine. Cards are always loaded in id order, so a deck's card order is stable.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Self

from pydantic import model_validator
from sqlmodel import Field, Relationship, SQLModel

from app.models.common import CardText, Description, TimestampColumn, Title, utcnow

if TYPE_CHECKING:
    from app.models.user import User


class DeckBase(SQLModel):
    title: str
    description: str | None = None


class Deck(DeckBase, table=True):
    __tablename__ = "decks"

    id: int | None = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=utcnow, sa_type=TimestampColumn)

    owner: "User" = Relationship(back_populates="decks", sa_relationship_kwargs={"lazy": "raise"})
    cards: list["Card"] = Relationship(
        back_populates="deck",
        sa_relationship_kwargs={
            "lazy": "raise",
            "cascade": "all, delete-orphan",
            "order_by": "Card.id",
        },
    )


class DeckCreate(DeckBase):
    title: Title
    description: Description | None = None


class DeckUpdate(SQLModel):
    """PATCH body: leave a field out to keep it. Sending title: null is rejected,
    since the column is NOT NULL (it would otherwise surface as a 500)."""

    title: Title | None = None
    description: Description | None = None

    @model_validator(mode="after")
    def title_cannot_be_null(self) -> Self:
        if "title" in self.model_fields_set and self.title is None:
            raise ValueError("title cannot be null")
        return self


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
    created_at: datetime = Field(default_factory=utcnow, sa_type=TimestampColumn)

    deck: Deck = Relationship(back_populates="cards", sa_relationship_kwargs={"lazy": "raise"})


class CardCreate(CardBase):
    question: CardText
    answer: CardText


class CardUpdate(SQLModel):
    """PATCH body: leave a field out to keep it; null is rejected (NOT NULL columns)."""

    question: CardText | None = None
    answer: CardText | None = None

    @model_validator(mode="after")
    def fields_cannot_be_null(self) -> Self:
        for name in ("question", "answer"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")
        return self


class CardPublic(CardBase):
    id: int
    deck_id: int
    created_at: datetime
