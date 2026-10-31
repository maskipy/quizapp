"""
Classes: a teacher's group of students, joined with a short code.

Named "classroom" in Python because `class` is a reserved word; the table is `classes`.
A teacher owns a class (teacher_id). Students are rows in class_memberships. The teacher
is not a membership row: ownership and membership are different things.
"""

import secrets
from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.common import ClassName, TimestampColumn, utcnow
from app.models.deck import DeckPublic

# 31 symbols, with the look-alikes (0/O, 1/I/L) removed so a code read off a board or a
# phone screen can't be mistyped. 31**8 is about 8.5e11 possible codes.
JOIN_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
JOIN_CODE_LENGTH = 8


def generate_join_code() -> str:
    # `secrets`, not `random`: join codes are a (weak) credential, so they must not be
    # predictable. The unique index guarantees correctness; a collision is not a
    # practical concern at this size.
    return "".join(secrets.choice(JOIN_CODE_ALPHABET) for _ in range(JOIN_CODE_LENGTH))


def normalize_join_code(raw: str) -> str:
    """Accept 'abcd-2345', 'ABCD 2345', ' abcd2345 ' -- whatever a student types."""
    return "".join(ch for ch in raw.upper() if ch.isalnum())


class ClassroomBase(SQLModel):
    name: str


class Classroom(ClassroomBase, table=True):
    __tablename__ = "classes"

    id: int | None = Field(default=None, primary_key=True)
    teacher_id: int = Field(foreign_key="users.id", index=True)
    join_code: str = Field(unique=True, index=True, default_factory=generate_join_code)
    created_at: datetime = Field(default_factory=utcnow, sa_type=TimestampColumn)


class ClassMembership(SQLModel, table=True):
    """One row = one student in one class. The primary key is the pair, so the database
    itself refuses to enroll the same student twice. ondelete="CASCADE" means deleting a
    class (or a user) removes their membership rows without any Python code."""

    __tablename__ = "class_memberships"

    class_id: int = Field(foreign_key="classes.id", primary_key=True, ondelete="CASCADE")
    user_id: int = Field(foreign_key="users.id", primary_key=True, index=True, ondelete="CASCADE")
    joined_at: datetime = Field(default_factory=utcnow, sa_type=TimestampColumn)


class ClassDeck(SQLModel, table=True):
    """One row = "this deck is shared with this class". A student can read a deck if and
    only if such a row exists for a class they belong to. Deleting the class or the deck
    removes the row (ondelete="CASCADE"), so stale shares can't linger."""

    __tablename__ = "class_decks"

    class_id: int = Field(foreign_key="classes.id", primary_key=True, ondelete="CASCADE")
    deck_id: int = Field(foreign_key="decks.id", primary_key=True, index=True, ondelete="CASCADE")
    shared_at: datetime = Field(default_factory=utcnow, sa_type=TimestampColumn)


class ClassroomCreate(ClassroomBase):
    name: ClassName


class JoinRequest(SQLModel):
    join_code: str = Field(min_length=1, max_length=32)


class ClassroomPublic(SQLModel):
    id: int
    name: str
    teacher_id: int
    created_at: datetime
    is_owner: bool
    # Only the class's teacher ever sees the code; for everyone else it is null.
    join_code: str | None = None
    member_count: int


class MemberPublic(SQLModel):
    id: int
    email: str
    full_name: str | None = None
    joined_at: datetime


class MemberPage(SQLModel):
    items: list[MemberPublic]
    total: int
    limit: int
    offset: int


class SharedDeckPublic(DeckPublic):
    shared_at: datetime
    card_count: int


class SharedDeckPage(SQLModel):
    items: list[SharedDeckPublic]
    total: int
    limit: int
    offset: int


class DeckShare(SQLModel):
    """Which of a teacher's classes a deck is shared with (for the share toggles)."""

    class_id: int
    name: str
    shared_at: datetime
