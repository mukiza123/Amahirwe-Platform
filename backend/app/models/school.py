import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class School(Base):
    """A pilot school. Students and teachers are linked to one school,
    which is what lets a teacher confirm or edit only their own students'
    profiles (SRS business rule 5.5)."""

    __tablename__ = "schools"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    district: Mapped[str] = mapped_column(String(120), nullable=False)
    province: Mapped[str] = mapped_column(String(120), nullable=False)

    # A student/teacher who can't find their school in the picker can
    # submit a new one themselves; it isn't usable by anyone else (i.e.
    # doesn't show up in the public /schools list) until an admin
    # approves it — same admin-gate pattern as mentor/provider
    # verification (SRS 5.5/5.6), just applied to school records.
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requested_by_user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
