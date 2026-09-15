"""
User models

- UserBase: fields shared by every variant below.
- User: the real table (table=True) -- adds id, hashed_password, is_active,
  created_at. This is the only one SQLModel.metadata / Alembic sees.
- UserCreate: what the /auth/register endpoint accepts -- a plain `password`
  field instead of `hashed_password`, since the client never sends a hash.
- UserPublic: what endpoints return -- deliberately has no password field
  at all, so a hashed password can never leak into an API response.
"""

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.deck import Deck


def utcnow() -> datetime:
    return datetime.now(UTC)


class UserBase(SQLModel):
    email: str = Field(unique=True, index=True)
    full_name: str | None = None


class User(UserBase, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    hashed_password: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=utcnow)

    decks: list["Deck"] = Relationship(
        back_populates="owner", sa_relationship_kwargs={"lazy": "raise"}
    )


class UserCreate(UserBase):
    password: str


class UserPublic(UserBase):
    id: int
    is_active: bool
    created_at: datetime
