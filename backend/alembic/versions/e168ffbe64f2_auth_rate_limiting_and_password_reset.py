"""auth rate limiting and password reset

Revision ID: e168ffbe64f2
Revises: f4a8b6d2e913
Create Date: 2026-09-19

"""

from alembic import op
import sqlalchemy as sa

revision = "e168ffbe64f2"
down_revision = "f4a8b6d2e913"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("email_verification_attempts", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "users",
        sa.Column("email_verification_last_sent_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("users", sa.Column("password_reset_code", sa.String(length=10), nullable=True))
    op.add_column(
        "users",
        sa.Column("password_reset_code_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("password_reset_attempts", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "users",
        sa.Column("password_reset_last_sent_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "password_reset_last_sent_at")
    op.drop_column("users", "password_reset_attempts")
    op.drop_column("users", "password_reset_code_expires_at")
    op.drop_column("users", "password_reset_code")
    op.drop_column("users", "email_verification_last_sent_at")
    op.drop_column("users", "email_verification_attempts")
