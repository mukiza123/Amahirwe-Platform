from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.models.school import School
from app.models.student import Student
from app.models.teacher import TeacherProfile
from app.models.user import User, UserRole
from app.schemas.student import StudentCreate, StudentRead, StudentUpdate

router = APIRouter(prefix="/api/students", tags=["students"])


@router.post("/me", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
def create_my_profile(
    payload: StudentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
):
    existing = db.query(Student).filter(Student.user_id == current_user.id).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You already have a student profile.")

    school = db.get(School, payload.school_id)
    if school is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="That school doesn't exist.")

    student = Student(
        user_id=current_user.id,
        school_id=payload.school_id,
        full_name=payload.full_name.strip(),
        age_range=payload.age_range,
        preferred_language=payload.preferred_language,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@router.get("/me", response_model=StudentRead)
def read_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
):
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No student profile yet. Complete your profile first.",
        )
    return student


@router.patch("/me", response_model=StudentRead)
def update_my_profile(
    payload: StudentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
):
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No student profile yet.")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(student, field, value)

    db.commit()
    db.refresh(student)
    return student


@router.get("/{student_id}", response_model=StudentRead)
def read_student(
    student_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found.")

    # Admins can view any student; a student can view their own profile;
    # a teacher can view students at their own school.
    is_owner = student.user_id == current_user.id
    is_school_teacher = False
    if current_user.role == UserRole.TEACHER:
        profile = db.query(TeacherProfile).filter(TeacherProfile.user_id == current_user.id).first()
        is_school_teacher = profile is not None and profile.school_id == student.school_id

    if current_user.role != UserRole.ADMIN and not is_owner and not is_school_teacher:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to do that.")

    return student
