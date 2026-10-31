"""add roles and classes

Revision ID: 8a0a668ccea9
Revises: ec8ca842e03f
Create Date: 2026-10-31 12:08:59.610216

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8a0a668ccea9"
down_revision: Union[str, Sequence[str], None] = "ec8ca842e03f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # server_default makes every existing account a student in the same statement that
    # adds the column; without it, a NOT NULL column can't be added to a table with rows.
    op.add_column("users", sa.Column("role", sa.String(), server_default="student", nullable=False))
    op.create_check_constraint("ck_users_role", "users", "role IN ('student', 'teacher')")

    op.create_table(
        "classes",
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=False),
        sa.Column("join_code", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_classes_teacher_id"), "classes", ["teacher_id"], unique=False)
    op.create_index(op.f("ix_classes_join_code"), "classes", ["join_code"], unique=True)

    op.create_table(
        "class_memberships",
        sa.Column("class_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("class_id", "user_id"),
    )
    op.create_index(
        op.f("ix_class_memberships_user_id"), "class_memberships", ["user_id"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_class_memberships_user_id"), table_name="class_memberships")
    op.drop_table("class_memberships")
    op.drop_index(op.f("ix_classes_join_code"), table_name="classes")
    op.drop_index(op.f("ix_classes_teacher_id"), table_name="classes")
    op.drop_table("classes")
    op.drop_constraint("ck_users_role", "users", type_="check")
    op.drop_column("users", "role")
