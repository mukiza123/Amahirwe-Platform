import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TalentArea(str, enum.Enum):
    TECHNOLOGY = "technology"
    LEADERSHIP = "leadership"
    CREATIVITY = "creativity"
    SPORT = "sport"
    ART = "art"
    PUBLIC_SPEAKING = "public_speaking"
    AGRICULTURE = "agriculture"


class TalentAssessment(Base):
    """One completed talent-discovery attempt by a student (SRS FR-1.1).

    Assessments are completed offline on the device and synced later, so
    sync_status tracks whether this copy has reached the server or is
    still only on the device.
    """

    __tablename__ = "talent_assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id"), nullable=False, index=True)
    language: Mapped[str] = mapped_column(String(2), default="rw", nullable=False)
    sync_status: Mapped[str] = mapped_column(String(20), default="synced", nullable=False)

    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class AssessmentAnswer(Base):
    """One answered question within a talent assessment.

    question_id and choice_id reference the static question bank in
    app/services/assessment_bank.py rather than a database table; the
    question content doesn't need to be admin-editable for this prototype.
    """

    __tablename__ = "assessment_answers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("talent_assessments.id"), nullable=False, index=True
    )
    question_id: Mapped[str] = mapped_column(String(20), nullable=False)
    choice_id: Mapped[str] = mapped_column(String(20), nullable=False)


class TalentResult(Base):
    """One identified strength from a completed assessment. An assessment
    can produce more than one result row: a student's top 1-3 strengths,
    ranked by how many of their answers pointed to that talent area."""

    __tablename__ = "talent_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("talent_assessments.id"), nullable=False, index=True
    )
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id"), nullable=False, index=True)
    talent_area: Mapped[TalentArea] = mapped_column(
        Enum(TalentArea, name="talent_area", values_callable=lambda cls: [e.value for e in cls]),
        nullable=False,
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
