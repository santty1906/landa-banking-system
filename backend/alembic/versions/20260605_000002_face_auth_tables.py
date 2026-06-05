"""add face auth tables

Revision ID: 20260605_000002
Revises: 20260604_000001
Create Date: 2026-06-05 00:00:02
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260605_000002"
down_revision: str | Sequence[str] | None = "20260604_000001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "face_embeddings",
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("encrypted_embedding", sa.String(), nullable=False),
        sa.Column("encryption_metadata", sa.JSON(), nullable=False),
        sa.Column("model_name", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("user_id", name=op.f("pk_face_embeddings")),
    )

    op.create_table(
        "auth_audit_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=True),
        sa.Column("method", sa.String(length=32), nullable=False),
        sa.Column("outcome", sa.String(length=16), nullable=False),
        sa.Column("reason_code", sa.String(length=64), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column("client_ip", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_auth_audit_logs")),
    )
    op.create_index(op.f("ix_auth_audit_logs_user_id"), "auth_audit_logs", ["user_id"], unique=False)
    op.create_index(op.f("ix_auth_audit_logs_created_at"), "auth_audit_logs", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_auth_audit_logs_created_at"), table_name="auth_audit_logs")
    op.drop_index(op.f("ix_auth_audit_logs_user_id"), table_name="auth_audit_logs")
    op.drop_table("auth_audit_logs")
    op.drop_table("face_embeddings")
