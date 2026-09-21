"""Allow each participant to hide a conversation independently.

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-07
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "chat_participants",
        sa.Column("hidden_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("chat_participants", "hidden_at")
