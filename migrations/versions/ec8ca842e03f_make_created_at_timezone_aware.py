"""make created_at timezone aware

Revision ID: ec8ca842e03f
Revises: cc5e616a06bf
Create Date: 2026-10-05 10:58:50.419700

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ec8ca842e03f"
down_revision: Union[str, Sequence[str], None] = "cc5e616a06bf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Existing values were stored as naive UTC. The explicit USING makes Postgres
    # read them as UTC no matter what the session time zone is -- without it, a
    # plain ALTER interprets them in the *session's* zone and shifts every row.
    for table in ("users", "decks", "cards"):
        op.alter_column(
            table,
            "created_at",
            type_=sa.DateTime(timezone=True),
            existing_type=sa.DateTime(),
            existing_nullable=False,
            postgresql_using="created_at AT TIME ZONE 'UTC'",
        )


def downgrade() -> None:
    """Downgrade schema."""
    for table in ("users", "decks", "cards"):
        op.alter_column(
            table,
            "created_at",
            type_=sa.DateTime(),
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=False,
            postgresql_using="created_at AT TIME ZONE 'UTC'",
        )
