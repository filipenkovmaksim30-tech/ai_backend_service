"""create contacts table

Revision ID: 477a1e7bfdfc
Revises: 
Create Date: 2026-07-22 14:51:41.281112

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '477a1e7bfdfc'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "contacts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("phone", sa.String(length=25), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("sentiment", sa.String(length=16), nullable=False),
        sa.Column("ai_summary", sa.String(length=500), nullable=False),
        sa.Column("ai_status", sa.String(length=16), nullable=False),
        sa.Column("owner_email_status", sa.String(length=16), nullable=False),
        sa.Column("user_email_status", sa.String(length=16), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("contacts")
