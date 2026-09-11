import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TeacherProfile(Base):
    """A teacher's school affiliation (SRS FR-1.2, FR-5): teachers create and
    manage student profiles at their own school, and review mentor match
    requests for those students."""

    __tablename__ = "teacher_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), unique=True, nullable=False)
    school_id: Mapped[str] = mapped_column(String(36), ForeignKey("schools.id"), nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
