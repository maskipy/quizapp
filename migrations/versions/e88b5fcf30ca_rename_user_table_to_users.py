"""rename user table to users

Revision ID: e88b5fcf30ca
Revises: e2bd7a8562a9
Create Date: 2026-09-10 18:23:33.847716

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "e88b5fcf30ca"
down_revision: Union[str, Sequence[str], None] = "e2bd7a8562a9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.rename_table("user", "users")


def downgrade() -> None:
    op.rename_table("users", "user")
