"""student guardians (parent-child link)

Revision ID: e27f4a9c1b58
Revises: d14a2b6e9c31
Create Date: 2026-09-12 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e27f4a9c1b58'
down_revision: Union[str, None] = 'd14a2b6e9c31'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "student_guardians",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_id", sa.String(length=36), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("guardian_user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("linked_by_teacher_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("student_id", "guardian_user_id", name="uq_student_guardian"),
    )
    op.create_index("ix_student_guardians_student_id", "student_guardians", ["student_id"])
    op.create_index("ix_student_guardians_guardian_user_id", "student_guardians", ["guardian_user_id"])


def downgrade() -> None:
    op.drop_index("ix_student_guardians_guardian_user_id", table_name="student_guardians")
    op.drop_index("ix_student_guardians_student_id", table_name="student_guardians")
    op.drop_table("student_guardians")
