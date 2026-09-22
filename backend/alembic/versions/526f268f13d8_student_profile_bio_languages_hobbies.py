"""student profile bio languages hobbies

Revision ID: 526f268f13d8
Revises: e168ffbe64f2
Create Date: 2026-09-22

"""

from alembic import op
import sqlalchemy as sa

revision = "526f268f13d8"
down_revision = "e168ffbe64f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("students", sa.Column("bio", sa.String(length=500), nullable=True))
    op.add_column("students", sa.Column("languages", sa.String(length=255), nullable=True))
    op.add_column("students", sa.Column("hobbies", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("students", "hobbies")
    op.drop_column("students", "languages")
    op.drop_column("students", "bio")
