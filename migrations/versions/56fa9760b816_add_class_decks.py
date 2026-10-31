"""add class decks

Revision ID: 56fa9760b816
Revises: 8a0a668ccea9
Create Date: 2026-10-31 12:45:25.953018

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "56fa9760b816"
down_revision: Union[str, Sequence[str], None] = "8a0a668ccea9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "class_decks",
        sa.Column("class_id", sa.Integer(), nullable=False),
        sa.Column("deck_id", sa.Integer(), nullable=False),
        sa.Column("shared_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["deck_id"], ["decks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("class_id", "deck_id"),
    )
    op.create_index(op.f("ix_class_decks_deck_id"), "class_decks", ["deck_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_class_decks_deck_id"), table_name="class_decks")
    op.drop_table("class_decks")
