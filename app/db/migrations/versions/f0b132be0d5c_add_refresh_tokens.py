"""add refresh tokens

Revision ID: f0b132be0d5c
Revises: 
Create Date: 
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "f0b132be0d5c"
down_revision = "0001_init"  # <-- ВАЖНО: тут надо оставить то, что было у тебя в файле
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_expires_at", "refresh_tokens", ["expires_at"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True)


def downgrade():
    # IF EXISTS — чтобы downgrade не падал, если таблица/индексы отсутствуют
    op.execute("DROP INDEX IF EXISTS ix_refresh_tokens_token_hash")
    op.execute("DROP INDEX IF EXISTS ix_refresh_tokens_expires_at")
    op.execute("DROP INDEX IF EXISTS ix_refresh_tokens_user_id")
    op.execute("DROP TABLE IF EXISTS refresh_tokens")

