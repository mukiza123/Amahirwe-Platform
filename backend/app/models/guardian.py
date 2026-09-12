import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class StudentGuardian(Base):
    """Links a parent/guardian account to a student (SRS: parents can
    view their child's progress). Only a teacher at the student's own
    school can create this link, the same trust boundary already used
    for creating student profiles, since this exposes a minor's data to
    another adult and can't be self-service."""

    __tablename__ = "student_guardians"
    __table_args__ = (UniqueConstraint("student_id", "guardian_user_id", name="uq_student_guardian"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id"), nullable=False, index=True)
    guardian_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    linked_by_teacher_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
