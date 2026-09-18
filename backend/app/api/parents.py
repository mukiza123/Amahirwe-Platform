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
    student_ids = [link.student_id for link in links]
    if not student_ids:
        return []

    # Batch every lookup by student id up front (a handful of queries
    # total) instead of re-querying per child, which used to mean 4
    # separate round trips for every single linked child.
    students_by_id = {s.id: s for s in db.query(Student).filter(Student.id.in_(student_ids)).all()}
    school_ids = {s.school_id for s in students_by_id.values()}
    schools_by_id = {sc.id: sc for sc in db.query(School).filter(School.id.in_(school_ids)).all()}

    # "Latest assessment id per student" (DISTINCT ON) joined straight
    # to its results is one round trip instead of "find latest
    # assessment ids" then "find results for those ids" as two —
    # SQLAlchemy compiles the subquery + join below into a single SQL
    # statement. Safe because assessments.py always creates a completed
    # assessment together with its (always ≥1) TalentResult rows in the
    # same commit, so a student appearing in `results` below is exactly
    # a student with a completed assessment.
    latest_assessment_subq = (
        db.query(TalentAssessment.id.label("assessment_id"), TalentAssessment.student_id)
        .filter(TalentAssessment.student_id.in_(student_ids))
        .order_by(TalentAssessment.student_id, TalentAssessment.completed_at.desc())
        .distinct(TalentAssessment.student_id)
        .subquery()
    )
    results = (
        db.query(latest_assessment_subq.c.student_id, latest_assessment_subq.c.assessment_id, TalentResult)
        .join(TalentResult, TalentResult.assessment_id == latest_assessment_subq.c.assessment_id)
        .order_by(TalentResult.rank)
        .all()
    )

    latest_assessment_id_by_student: dict = {}
    results_by_assessment_id: dict = {}
    for student_id, assessment_id, result in results:
        latest_assessment_id_by_student[student_id] = assessment_id
        results_by_assessment_id.setdefault(assessment_id, []).append(result)

    latest_matches = (
        db.query(MentorMatch)
        .filter(MentorMatch.student_id.in_(student_ids))
        .order_by(MentorMatch.created_at.desc())
        .all()
    )
    latest_match_by_student = {}
    for match in latest_matches:
        latest_match_by_student.setdefault(match.student_id, match)

    children = []
    for link in links:
        student = students_by_id.get(link.student_id)
        if student is None:
            continue
        school = schools_by_id.get(student.school_id)
        latest_assessment_id = latest_assessment_id_by_student.get(student.id)
        top_talents = [
            ChildTalentSummary(
                talent_area=r.talent_area,
                score=r.score,
                rank=r.rank,
                explanation=explanation_for(r.talent_area),
            )
            for r in results_by_assessment_id.get(latest_assessment_id, [])
        ] if latest_assessment_id is not None else []
        match = latest_match_by_student.get(student.id)

        children.append(
            ChildRead(
                id=student.id,
                full_name=student.full_name,
                age_range=student.age_range,
                school_name=school.name if school else "",
                has_completed_assessment=latest_assessment_id is not None,
                top_talents=top_talents,
                mentor_match_status=match.status.value if match else None,
            )
        )

    return children
