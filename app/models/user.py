"""
User models, following SQLModel's "multiple models" pattern:

- UserBase: fields shared by every variant below.
- User: the real table (table=True).
- UserCreate: what /auth/register accepts. This is where input is validated.
- UserPublic: what endpoints return -- it has no password field at all, so a hash
  can never leak into a response.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import EmailStr, field_validator
from sqlmodel import Field, Relationship, SQLModel

from app.models.common import Name, TimestampColumn, utcnow

if TYPE_CHECKING:
    from app.models.deck import Deck


class UserBase(SQLModel):
    email: str = Field(unique=True, index=True)
    full_name: str | None = None


class User(UserBase, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    hashed_password: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=utcnow, sa_type=TimestampColumn)

    decks: list["Deck"] = Relationship(
        back_populates="owner", sa_relationship_kwargs={"lazy": "raise"}
    )


class UserCreate(UserBase):
    # Format is checked on the way *in* only. UserPublic keeps a plain str, so an old
    # row with an odd address can never make a response fail validation (a 500).
    email: EmailStr
    full_name: Name | None = None
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, value: str) -> str:
        # The unique index is case-sensitive, so "Ana@x.com" and "ana@x.com" would be
        # two accounts. Store lowercase; login lowercases what was typed too.
        return value.lower()


class UserPublic(UserBase):
    id: int
    is_active: bool
    created_at: datetime
