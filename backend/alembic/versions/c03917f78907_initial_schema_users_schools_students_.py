"""initial schema: users, schools, students, talent assessments

Revision ID: c03917f78907
Revises:
Create Date: 2026-09-10 18:13:21.115102

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c03917f78907'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


user_role_enum = sa.Enum(
    "student", "teacher", "mentor", "provider", "admin", "parent",
    name="user_role",
)
talent_area_enum = sa.Enum(
    "technology", "leadership", "creativity", "sport", "art", "public_speaking", "agriculture",
    name="talent_area",
)


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", user_role_enum, nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "schools",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("district", sa.String(length=120), nullable=False),
        sa.Column("province", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "students",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), unique=True, nullable=True),
        sa.Column("school_id", sa.String(length=36), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("created_by_teacher_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("age_range", sa.String(length=10), nullable=False),
        sa.Column("preferred_language", sa.String(length=2), nullable=False, server_default="rw"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_students_school_id", "students", ["school_id"])

    op.create_table(
        "talent_assessments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_id", sa.String(length=36), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("language", sa.String(length=2), nullable=False, server_default="rw"),
        sa.Column("sync_status", sa.String(length=20), nullable=False, server_default="synced"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_talent_assessments_student_id", "talent_assessments", ["student_id"])

    op.create_table(
        "assessment_answers",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("assessment_id", sa.String(length=36), sa.ForeignKey("talent_assessments.id"), nullable=False),
        sa.Column("question_id", sa.String(length=20), nullable=False),
        sa.Column("choice_id", sa.String(length=20), nullable=False),
    )
    op.create_index("ix_assessment_answers_assessment_id", "assessment_answers", ["assessment_id"])

    op.create_table(
        "talent_results",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("assessment_id", sa.String(length=36), sa.ForeignKey("talent_assessments.id"), nullable=False),
        sa.Column("student_id", sa.String(length=36), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("talent_area", talent_area_enum, nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_talent_results_assessment_id", "talent_results", ["assessment_id"])
    op.create_index("ix_talent_results_student_id", "talent_results", ["student_id"])


def downgrade() -> None:
    op.drop_index("ix_talent_results_student_id", table_name="talent_results")
    op.drop_index("ix_talent_results_assessment_id", table_name="talent_results")
    op.drop_table("talent_results")

    op.drop_index("ix_assessment_answers_assessment_id", table_name="assessment_answers")
    op.drop_table("assessment_answers")

    op.drop_index("ix_talent_assessments_student_id", table_name="talent_assessments")
    op.drop_table("talent_assessments")

    op.drop_index("ix_students_school_id", table_name="students")
    op.drop_table("students")

    op.drop_table("schools")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    talent_area_enum.drop(op.get_bind(), checkfirst=True)
    user_role_enum.drop(op.get_bind(), checkfirst=True)
