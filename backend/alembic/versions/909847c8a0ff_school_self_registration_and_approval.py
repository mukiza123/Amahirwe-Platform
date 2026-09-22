"""school self-registration and admin approval

Revision ID: 909847c8a0ff
Revises: 526f268f13d8
Create Date: 2026-09-22

"""

from alembic import op
import sqlalchemy as sa

revision = "909847c8a0ff"
down_revision = "526f268f13d8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Existing rows are the pilot's real, already-vetted schools —
    # server_default backfills them as approved. New rows (student/
    # teacher self-submissions) get the Python-side default of False
    # instead, since the ORM always sends an explicit value on insert.
    op.add_column(
        "schools",
        sa.Column("is_approved", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column("schools", sa.Column("requested_by_user_id", sa.String(length=36), nullable=True))
    op.create_foreign_key(
        "fk_schools_requested_by_user_id_users",
        "schools",
        "users",
        ["requested_by_user_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_schools_requested_by_user_id_users", "schools", type_="foreignkey")
    op.drop_column("schools", "requested_by_user_id")
    op.drop_column("schools", "is_approved")
