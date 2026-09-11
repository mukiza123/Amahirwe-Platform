"""teachers, mentors, mentor matches, opportunities, audit log, notifications

Revision ID: d14a2b6e9c31
Revises: c03917f78907
Create Date: 2026-09-10 19:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM


# revision identifiers, used by Alembic.
revision: str = 'd14a2b6e9c31'
down_revision: Union[str, None] = 'c03917f78907'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# create_type=False only has an effect on the dialect-specific PG_ENUM
# (the generic sa.Enum silently ignores it), and is needed here because
# each type is attached to more than one table below; without it, each
# attachment after the first tries to CREATE TYPE again and fails.
talent_area_enum = PG_ENUM(
    "technology", "leadership", "creativity", "sport", "art", "public_speaking", "agriculture",
    name="talent_area",
    create_type=False,
)
match_status_enum = PG_ENUM("pending", "approved", "rejected", name="match_status", create_type=False)


def upgrade() -> None:
    # Both enum types are attached to columns in more than one table below;
    # each attachment defaults to create_type=True, which would try (and
    # fail on) a duplicate CREATE TYPE for the second and third use. So the
    # columns above set create_type=False, and the types are created here,
    # exactly once, explicitly. talent_area already exists from the
    # previous migration, so only match_status needs creating.
    match_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "teacher_profiles",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), unique=True, nullable=False),
        sa.Column("school_id", sa.String(length=36), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_teacher_profiles_school_id", "teacher_profiles", ["school_id"])

    op.create_table(
        "mentors",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), unique=True, nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("district", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "mentor_expertise",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("mentor_id", sa.String(length=36), sa.ForeignKey("mentors.id"), nullable=False),
        sa.Column("talent_area", talent_area_enum, nullable=False),
    )
    op.create_index("ix_mentor_expertise_mentor_id", "mentor_expertise", ["mentor_id"])

    op.create_table(
        "mentor_matches",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_id", sa.String(length=36), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("mentor_id", sa.String(length=36), sa.ForeignKey("mentors.id"), nullable=False),
        sa.Column("talent_area", talent_area_enum, nullable=False),
        sa.Column("status", match_status_enum, nullable=False, server_default="pending"),
        sa.Column("reviewed_by_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_mentor_matches_student_id", "mentor_matches", ["student_id"])
    op.create_index("ix_mentor_matches_mentor_id", "mentor_matches", ["mentor_id"])

    op.create_table(
        "opportunities",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("provider_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("talent_area", talent_area_enum, nullable=True),
        sa.Column("location", sa.String(length=160), nullable=False),
        sa.Column("deadline", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_opportunities_provider_id", "opportunities", ["provider_id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("actor_user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(length=60), nullable=False),
        sa.Column("target_type", sa.String(length=40), nullable=False),
        sa.Column("target_id", sa.String(length=36), nullable=False),
        sa.Column("detail", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])

    op.create_table(
        "notifications",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("message", sa.String(length=255), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")

    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("ix_opportunities_provider_id", table_name="opportunities")
    op.drop_table("opportunities")

    op.drop_index("ix_mentor_matches_mentor_id", table_name="mentor_matches")
    op.drop_index("ix_mentor_matches_student_id", table_name="mentor_matches")
    op.drop_table("mentor_matches")

    op.drop_index("ix_mentor_expertise_mentor_id", table_name="mentor_expertise")
    op.drop_table("mentor_expertise")

    op.drop_table("mentors")

    op.drop_index("ix_teacher_profiles_school_id", table_name="teacher_profiles")
    op.drop_table("teacher_profiles")

    match_status_enum.drop(op.get_bind(), checkfirst=True)
