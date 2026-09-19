"""email verification (code sent to a user's email on registration)

Revision ID: f4a8b6d2e913
Revises: e27f4a9c1b58
Create Date: 2026-09-18 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f4a8b6d2e913'
down_revision: Union[str, None] = 'e27f4a9c1b58'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # server_default=true backfills every existing account (including
    # anyone who registered before this feature existed) as already
    # verified, so nobody already using the app gets locked out. New
    # accounts created through the ORM explicitly pass False (the
    # Python-side model default), overriding this server default.
    op.add_column(
        "users",
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column("users", sa.Column("email_verification_code", sa.String(length=10), nullable=True))
    op.add_column(
        "users", sa.Column("email_verification_code_expires_at", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("users", "email_verification_code_expires_at")
    op.drop_column("users", "email_verification_code")
    op.drop_column("users", "email_verified")
