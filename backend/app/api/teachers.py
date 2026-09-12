from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.database import get_db
from app.models.audit import AuditLog, Notification
from app.models.guardian import StudentGuardian
from app.models.mentor import MatchStatus, MentorMatch
from app.models.school import School
from app.models.student import Student
from app.models.talent import TalentAssessment, TalentResult
from app.models.teacher import TeacherProfile
from app.models.user import User, UserRole
from app.schemas.guardian import GuardianLinkCreate, GuardianLinkRead
from app.schemas.mentor import MatchRead
from app.schemas.stats import StudentSummary, TeacherOverview
from app.schemas.teacher import (
    TeacherProfileCreate,
    TeacherProfileRead,
    TeacherStudentCreate,
    TeacherStudentRead,
)

router = APIRouter(prefix="/api/teachers", tags=["teachers"])


def _get_own_profile(db: Session, current_user: User) -> TeacherProfile:
    profile = db.query(TeacherProfile).filter(TeacherProfile.user_id == current_user.id).first()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No teacher profile yet. Complete your profile first.",
        )
    return profile


@router.post("/me", response_model=TeacherProfileRead, status_code=status.HTTP_201_CREATED)
def create_my_profile(
    payload: TeacherProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.TEACHER)),
):
    existing = db.query(TeacherProfile).filter(TeacherProfile.user_id == current_user.id).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You already have a teacher profile.")

    school = db.get(School, payload.school_id)
    if school is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="That school doesn't exist.")

    profile = TeacherProfile(user_id=current_user.id, school_id=payload.school_id)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/me", response_model=TeacherProfileRead)
def read_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.TEACHER)),
):
    return _get_own_profile(db, current_user)


@router.get("/me/students", response_model=List[TeacherStudentRead])
def list_my_students(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.TEACHER)),
):
    profile = _get_own_profile(db, current_user)
    return (
        db.query(Student)
        .filter(Student.school_id == profile.school_id)
        .order_by(Student.full_name)
        .all()
    )


@router.post("/students", response_model=TeacherStudentRead, status_code=status.HTTP_201_CREATED)
def create_student_for_my_school(
    payload: TeacherStudentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.TEACHER)),
):
    profile = _get_own_profile(db, current_user)

    student = Student(
        school_id=profile.school_id,
        created_by_teacher_id=current_user.id,
        full_name=payload.full_name.strip(),
        age_range=payload.age_range,
        preferred_language=payload.preferred_language,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@router.get("/me/matches", response_model=List[MatchRead])
def list_matches_for_my_school(
    match_status: Optional[MatchStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.TEACHER)),
):
    """Mentor match requests for students at this teacher's school, for
    review (SRS 5.5). Contact details are never included here; approving
    the match is what unlocks them, via GET /api/matches/{id}."""

    profile = _get_own_profile(db, current_user)
    query = (
        db.query(MentorMatch)
        .join(Student, Student.id == MentorMatch.student_id)
        .filter(Student.school_id == profile.school_id)
    )
    if match_status is not None:
        query = query.filter(MentorMatch.status == match_status)
    return query.order_by(MentorMatch.created_at.desc()).all()


def _top_result(db: Session, student_id: str):
    latest = (
        db.query(TalentAssessment)
        .filter(TalentAssessment.student_id == student_id)
        .order_by(TalentAssessment.completed_at.desc())
        .first()
    )
    if latest is None:
        return None
    return (
        db.query(TalentResult)
        .filter(TalentResult.assessment_id == latest.id, TalentResult.rank == 1)
        .first()
    )


@router.get("/me/overview", response_model=TeacherOverview)
def read_my_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.TEACHER)),
):
    """Real, computed numbers for the teacher's Home dashboard: no
    fabricated metrics, everything here is a direct query result."""

    profile = _get_own_profile(db, current_user)
    students = db.query(Student).filter(Student.school_id == profile.school_id).order_by(Student.full_name).all()

    summaries = []
    with_assessment = 0
    for student in students:
        top = _top_result(db, student.id)
        if top is not None:
            with_assessment += 1
        summaries.append(
            StudentSummary(
                id=student.id,
                full_name=student.full_name,
                age_range=student.age_range,
                is_registered=student.user_id is not None,
                top_talent_area=top.talent_area if top else None,
                top_score=top.score if top else None,
            )
        )

    pending_count = (
        db.query(MentorMatch)
        .join(Student, Student.id == MentorMatch.student_id)
        .filter(Student.school_id == profile.school_id, MentorMatch.status == MatchStatus.PENDING)
        .count()
    )

    return TeacherOverview(
        student_count=len(students),
        pending_match_count=pending_count,
        students_with_assessment_count=with_assessment,
        students=summaries,
    )


@router.post(
    "/students/{student_id}/guardians", response_model=GuardianLinkRead, status_code=status.HTTP_201_CREATED
)
def link_guardian(
    student_id: str,
    payload: GuardianLinkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.TEACHER)),
):
    """Links a parent/guardian account to a student at this teacher's
    school (SRS: safeguarding means only a teacher, not the parent
    themselves, can create this link)."""

    profile = _get_own_profile(db, current_user)
    student = db.get(Student, student_id)
    if student is None or student.school_id != profile.school_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found at your school.")

    guardian = db.query(User).filter(User.email == payload.guardian_email.lower()).first()
    if guardian is None or guardian.role != UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No parent/guardian account found with that email. They need to register first.",
        )

    existing = (
        db.query(StudentGuardian)
        .filter(StudentGuardian.student_id == student.id, StudentGuardian.guardian_user_id == guardian.id)
        .first()
    )
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="That guardian is already linked.")

    link = StudentGuardian(student_id=student.id, guardian_user_id=guardian.id, linked_by_teacher_id=current_user.id)
    db.add(link)
    db.add(
        AuditLog(
            actor_user_id=current_user.id,
            action="guardian_linked",
            target_type="student",
            target_id=student.id,
            detail=f"Linked guardian {guardian.email}",
        )
    )
    db.add(
        Notification(
            user_id=guardian.id,
            message=f"You've been linked as a guardian for {student.full_name}. You can now see their progress.",
        )
    )
    db.commit()
    db.refresh(link)

    return GuardianLinkRead(
        id=link.id,
        student_id=link.student_id,
        guardian_user_id=link.guardian_user_id,
        guardian_name=guardian.full_name,
        guardian_email=guardian.email,
        created_at=link.created_at,
    )
