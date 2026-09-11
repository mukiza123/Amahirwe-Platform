import enum
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.talent import TalentArea


class MatchStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Mentor(Base):
    """A mentor's public profile (SRS 5.5): verification happens on the
    shared users.is_verified flag set by an admin, not duplicated here."""

    __tablename__ = "mentors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), unique=True, nullable=False)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    district: Mapped[str] = mapped_column(String(120), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    expertise: Mapped[list["MentorExpertise"]] = relationship(
        "MentorExpertise", cascade="all, delete-orphan", lazy="selectin"
    )
    user: Mapped["User"] = relationship("User", lazy="joined", viewonly=True)  # noqa: F821


class MentorExpertise(Base):
    """One talent area a mentor can guide students in. A mentor can list
    more than one, which is what the matching algorithm searches against."""

    __tablename__ = "mentor_expertise"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mentor_id: Mapped[str] = mapped_column(String(36), ForeignKey("mentors.id"), nullable=False, index=True)
    talent_area: Mapped[TalentArea] = mapped_column(
        Enum(TalentArea, name="talent_area", values_callable=lambda cls: [e.value for e in cls]),
        nullable=False,
    )


class MentorMatch(Base):
    """A proposed pairing between a student and a mentor, always starting
    pending. A teacher or admin at the student's school must approve it
    before mentor contact details are shared (SRS 5.5: no unsupervised
    contact between students and mentors)."""

    __tablename__ = "mentor_matches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id"), nullable=False, index=True)
    mentor_id: Mapped[str] = mapped_column(String(36), ForeignKey("mentors.id"), nullable=False, index=True)
    talent_area: Mapped[TalentArea] = mapped_column(
        Enum(TalentArea, name="talent_area", values_callable=lambda cls: [e.value for e in cls]),
        nullable=False,
    )
    status: Mapped[MatchStatus] = mapped_column(
        Enum(MatchStatus, name="match_status", values_callable=lambda cls: [e.value for e in cls]),
        default=MatchStatus.PENDING,
        nullable=False,
    )
    reviewed_by_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
