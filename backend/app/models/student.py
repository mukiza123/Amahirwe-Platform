import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Student(Base):
    """A student's profile.

    A profile can exist before the student has an account of their own:
    SRS FR-1.2 lets a teacher start a profile for a student who's shy about
    registering themselves, and the student confirms it later by
    registering and claiming it. So user_id stays nullable until that
    happens; created_by_teacher_id records who started it in the meantime.
    """

    __tablename__ = "students"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), unique=True, nullable=True)
    school_id: Mapped[str] = mapped_column(String(36), ForeignKey("schools.id"), nullable=False, index=True)
    created_by_teacher_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    age_range: Mapped[str] = mapped_column(String(10), nullable=False)  # e.g. "12-14", "15-16", "17-19"
    preferred_language: Mapped[str] = mapped_column(String(2), default="rw", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
