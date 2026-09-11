from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.database import get_db
from app.models.mentor import MatchStatus, MentorMatch
from app.models.school import School
from app.models.student import Student
from app.models.teacher import TeacherProfile
from app.models.user import User, UserRole
from app.schemas.mentor import MatchRead
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
