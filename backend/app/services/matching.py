"""Rule-based mentor matching (SRS 5.5): match a student's top talent
result to a verified mentor who lists that same talent area as expertise.
Deliberately simple, not a scored/weighted recommender."""

from typing import Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.mentor import Mentor, MentorExpertise, MentorMatch, MatchStatus
from app.models.talent import TalentArea, TalentAssessment, TalentResult
from app.models.user import User


def find_candidate_mentor(db: Session, student_id: str, talent_area: TalentArea) -> Optional[Mentor]:
    """The first verified mentor with matching expertise who doesn't
    already have a pending or approved match with this student."""

    already_matched_mentor_ids = {
        row.mentor_id
        for row in db.query(MentorMatch.mentor_id)
        .filter(
            MentorMatch.student_id == student_id,
            MentorMatch.status.in_([MatchStatus.PENDING, MatchStatus.APPROVED]),
        )
        .all()
    }

    query = (
        db.query(Mentor)
        .join(User, User.id == Mentor.user_id)
        .join(MentorExpertise, MentorExpertise.mentor_id == Mentor.id)
        .filter(and_(User.is_verified.is_(True), MentorExpertise.talent_area == talent_area))
    )

    for mentor in query.all():
        if mentor.id not in already_matched_mentor_ids:
            return mentor

    return None


def top_talent_area(db: Session, student_id: str) -> Optional[TalentArea]:
    """The talent area from the student's most recently completed
    assessment's rank-1 result, or None if they haven't completed one."""

    latest = (
        db.query(TalentAssessment)
        .filter(TalentAssessment.student_id == student_id)
        .order_by(TalentAssessment.completed_at.desc())
        .first()
    )
    if latest is None:
        return None

    top_result = (
        db.query(TalentResult)
        .filter(TalentResult.assessment_id == latest.id, TalentResult.rank == 1)
        .first()
    )
    return top_result.talent_area if top_result else None
