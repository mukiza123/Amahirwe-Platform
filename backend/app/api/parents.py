from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.database import get_db
from app.models.guardian import StudentGuardian
from app.models.mentor import MentorMatch
from app.models.school import School
from app.models.student import Student
from app.models.talent import TalentAssessment, TalentResult
from app.models.user import User, UserRole
from app.schemas.guardian import ChildRead, ChildTalentSummary
from app.services.talent_scoring import explanation_for

router = APIRouter(prefix="/api/parents", tags=["parents"])


@router.get("/me/children", response_model=List[ChildRead])
def list_my_children(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.PARENT)),
):
    """Real progress data for every student this parent has been linked
    to by a teacher (SRS: parents can follow their child's progress)."""

    links = db.query(StudentGuardian).filter(StudentGuardian.guardian_user_id == current_user.id).all()

    children = []
    for link in links:
        student = db.get(Student, link.student_id)
        if student is None:
            continue
        school = db.get(School, student.school_id)

        latest = (
            db.query(TalentAssessment)
            .filter(TalentAssessment.student_id == student.id)
            .order_by(TalentAssessment.completed_at.desc())
            .first()
        )
        top_talents = []
        if latest is not None:
            results = (
                db.query(TalentResult)
                .filter(TalentResult.assessment_id == latest.id)
                .order_by(TalentResult.rank)
                .all()
            )
            top_talents = [
                ChildTalentSummary(
                    talent_area=r.talent_area,
                    score=r.score,
                    rank=r.rank,
                    explanation=explanation_for(r.talent_area),
                )
                for r in results
            ]

        match = (
            db.query(MentorMatch)
            .filter(MentorMatch.student_id == student.id)
            .order_by(MentorMatch.created_at.desc())
            .first()
        )

        children.append(
            ChildRead(
                id=student.id,
                full_name=student.full_name,
                age_range=student.age_range,
                school_name=school.name if school else "",
                has_completed_assessment=latest is not None,
                top_talents=top_talents,
                mentor_match_status=match.status.value if match else None,
            )
        )

    return children
