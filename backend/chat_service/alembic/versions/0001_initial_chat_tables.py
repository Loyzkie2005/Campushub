"""Create initial chat tables.

Revision ID: 0001
Revises:
Create Date: 2026-07-27
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "chat_conversations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("direct_key", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("direct_key"),
    )
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "conversation_id",
            sa.Integer(),
            sa.ForeignKey("chat_conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sender_actor_key", sa.String(length=255), nullable=False),
        sa.Column("sender_name", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(body) BETWEEN 1 AND 2000",
            name="ck_chat_message_body_length",
        ),
    )
    op.create_index(
        "ix_chat_message_conversation_id_id",
        "chat_messages",
        ["conversation_id", "id"],
    )
    op.create_table(
        "chat_participants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "conversation_id",
            sa.Integer(),
            sa.ForeignKey("chat_conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("actor_key", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "last_read_message_id",
            sa.Integer(),
            sa.ForeignKey("chat_messages.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.UniqueConstraint(
            "conversation_id",
            "actor_key",
            name="uq_chat_participant_actor",
        ),
    )
    op.create_index(
        "ix_chat_participant_actor_key", "chat_participants", ["actor_key"]
    )


def downgrade() -> None:
    op.drop_index("ix_chat_participant_actor_key", table_name="chat_participants")
    op.drop_table("chat_participants")
    op.drop_index(
        "ix_chat_message_conversation_id_id", table_name="chat_messages"
    )
    op.drop_table("chat_messages")
    op.drop_table("chat_conversations")
