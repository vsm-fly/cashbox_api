"""init

Revision ID: 0001_init
Revises:
Create Date: 2026-02-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    # Enums: создаём типы вручную один раз, а в колонках используем эти же объекты
    user_role = postgresql.ENUM(
        "admin", "user", "viewer",
        name="user_role",
        create_type=False,
    )
    tx_type = postgresql.ENUM(
        "income", "expense",
        name="tx_type",
        create_type=False,
    )
    job_type = postgresql.ENUM(
        "export_transactions", "print_ko1", "print_ko2",
        name="job_type",
        create_type=False,
    )
    job_status = postgresql.ENUM(
        "queued", "running", "done", "failed", "canceled",
        name="job_status",
        create_type=False,
    )

    user_role.create(bind, checkfirst=True)
    tx_type.create(bind, checkfirst=True)
    job_type.create(bind, checkfirst=True)
    job_status.create(bind, checkfirst=True)

    # users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False, server_default=sa.text("'user'")),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_role", "users", ["role"])

    # clients
    op.create_table(
        "clients",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
    )
    op.create_index("ix_clients_name", "clients", ["name"])

    # transactions
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("type", tx_type, nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("rate", sa.Numeric(18, 6), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id"), nullable=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_transactions_type", "transactions", ["type"])
    op.create_index("ix_transactions_currency", "transactions", ["currency"])
    op.create_index("ix_transactions_client_id", "transactions", ["client_id"])
    op.create_index("ix_transactions_created_by", "transactions", ["created_by"])
    op.create_index("ix_transactions_timestamp", "transactions", ["timestamp"])

    # audit_logs
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("entity", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_entity", "audit_logs", ["entity"])
    op.create_index("ix_audit_logs_entity_id", "audit_logs", ["entity_id"])
    op.create_index("ix_audit_logs_timestamp", "audit_logs", ["timestamp"])

    # jobs
    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("type", job_type, nullable=False),
        sa.Column("status", job_status, nullable=False, server_default=sa.text("'queued'")),
        sa.Column("progress", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "params",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_by", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_jobs_type", "jobs", ["type"])
    op.create_index("ix_jobs_status", "jobs", ["status"])
    op.create_index("ix_jobs_created_by", "jobs", ["created_by"])
    op.create_index("ix_jobs_created_at", "jobs", ["created_at"])
    op.create_index("ix_jobs_created_by_created_at", "jobs", ["created_by", "created_at"])


def downgrade() -> None:
    # drop jobs
    op.drop_index("ix_jobs_created_by_created_at", table_name="jobs")
    op.drop_index("ix_jobs_created_at", table_name="jobs")
    op.drop_index("ix_jobs_created_by", table_name="jobs")
    op.drop_index("ix_jobs_status", table_name="jobs")
    op.drop_index("ix_jobs_type", table_name="jobs")
    op.drop_table("jobs")

    # drop audit_logs
    op.drop_index("ix_audit_logs_timestamp", table_name="audit_logs")
    op.drop_index("ix_audit_logs_entity_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_entity", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_user_id", table_name="audit_logs")
    op.drop_table("audit_logs")

    # drop transactions
    op.drop_index("ix_transactions_timestamp", table_name="transactions")
    op.drop_index("ix_transactions_created_by", table_name="transactions")
    op.drop_index("ix_transactions_client_id", table_name="transactions")
    op.drop_index("ix_transactions_currency", table_name="transactions")
    op.drop_index("ix_transactions_type", table_name="transactions")
    op.drop_table("transactions")

    # drop clients
    op.drop_index("ix_clients_name", table_name="clients")
    op.drop_table("clients")

    # drop users
    op.drop_index("ix_users_role", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    # drop enum types (safe)
    op.execute("DROP TYPE IF EXISTS job_status")
    op.execute("DROP TYPE IF EXISTS job_type")
    op.execute("DROP TYPE IF EXISTS tx_type")
    op.execute("DROP TYPE IF EXISTS user_role")
