from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.models.audit import AuditLog, Notification
from app.models.mentor import MatchStatus, Mentor, MentorMatch
from app.models.student import Student
from app.models.teacher import TeacherProfile
from app.models.user import User, UserRole
from app.schemas.mentor import MatchRead
from app.services.matching import find_candidate_mentor, top_talent_area

router = APIRouter(prefix="/api/matches", tags=["matches"])


def _to_read(match: MentorMatch, db: Session, *, include_contact: bool) -> MatchRead:
    data = MatchRead.model_validate(match)
    if include_contact and match.status == MatchStatus.APPROVED:
        student = db.get(Student, match.student_id)
        mentor = db.get(Mentor, match.mentor_id)
        if student is not None:
            data.student_name = student.full_name
            if student.user_id:
                student_user = db.get(User, student.user_id)
                data.student_contact_email = student_user.email if student_user else None
        if mentor is not None:
            mentor_user = db.get(User, mentor.user_id)
            data.mentor_name = mentor_user.full_name if mentor_user else None
            data.mentor_contact_email = mentor_user.email if mentor_user else None
    return data


def _authorize_reviewer(db: Session, current_user: User, match: MentorMatch) -> None:
    """A match can only be approved/rejected by the teacher at the
    matched student's own school, or an admin (SRS 5.5)."""

    if current_user.role == UserRole.ADMIN:
        return
    if current_user.role == UserRole.TEACHER:
        student = db.get(Student, match.student_id)
        profile = db.query(TeacherProfile).filter(TeacherProfile.user_id == current_user.id).first()
        if student is not None and profile is not None and student.school_id == profile.school_id:
            return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to do that.")


@router.post("/find", response_model=MatchRead, status_code=status.HTTP_201_CREATED)
def find_a_mentor(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
):
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complete your student profile first.")

    area = top_talent_area(db, student.id)
    if area is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complete your talent assessment first so we know what to match you on.",
        )

    mentor = find_candidate_mentor(db, student.id, area)
    if mentor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No mentor is available for that talent area right now. Please check back later.",
        )

    match = MentorMatch(student_id=student.id, mentor_id=mentor.id, talent_area=area, status=MatchStatus.PENDING)
    db.add(match)
    db.flush()

    db.add(
        AuditLog(
            actor_user_id=current_user.id,
            action="match_requested",
            target_type="mentor_match",
            target_id=match.id,
            detail=f"Requested a {area.value} mentor match.",
        )
    )
    for teacher_profile in db.query(TeacherProfile).filter(TeacherProfile.school_id == student.school_id).all():
        db.add(
            Notification(
                user_id=teacher_profile.user_id,
                message=f"{student.full_name} requested a mentor match ({area.value}). Review it in your dashboard.",
            )
        )

    db.commit()
    db.refresh(match)
    return _to_read(match, db, include_contact=False)


@router.get("/me", response_model=List[MatchRead])
def list_my_matches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.STUDENT:
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        matches = (
            db.query(MentorMatch).filter(MentorMatch.student_id == student.id).order_by(MentorMatch.created_at.desc()).all()
            if student
            else []
        )
    elif current_user.role == UserRole.MENTOR:
        mentor = db.query(Mentor).filter(Mentor.user_id == current_user.id).first()
        matches = (
            db.query(MentorMatch).filter(MentorMatch.mentor_id == mentor.id).order_by(MentorMatch.created_at.desc()).all()
            if mentor
            else []
        )
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to do that.")

    return [_to_read(m, db, include_contact=True) for m in matches]


@router.get("/{match_id}", response_model=MatchRead)
def read_match(
    match_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    match = db.get(MentorMatch, match_id)
    if match is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found.")

    if current_user.role == UserRole.STUDENT:
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        if student is None or match.student_id != student.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to do that.")
    elif current_user.role == UserRole.MENTOR:
        mentor = db.query(Mentor).filter(Mentor.user_id == current_user.id).first()
        if mentor is None or match.mentor_id != mentor.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to do that.")
    else:
        _authorize_reviewer(db, current_user, match)

    return _to_read(match, db, include_contact=True)


@router.patch("/{match_id}/approve", response_model=MatchRead)
def approve_match(
    match_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.ADMIN)),
):
    match = db.get(MentorMatch, match_id)
    if match is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found.")
    _authorize_reviewer(db, current_user, match)

    if match.status != MatchStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This match has already been reviewed.")

    match.status = MatchStatus.APPROVED
    match.reviewed_by_id = current_user.id
    match.reviewed_at = datetime.now(timezone.utc)

    student = db.get(Student, match.student_id)
    mentor = db.get(Mentor, match.mentor_id)
    if student and student.user_id:
        db.add(Notification(user_id=student.user_id, message="Your mentor match was approved! You can now see your mentor's contact details."))
    if mentor:
        db.add(Notification(user_id=mentor.user_id, message="A mentor match was approved! You can now see the student's contact details."))
    db.add(
        AuditLog(
            actor_user_id=current_user.id,
            action="match_approved",
            target_type="mentor_match",
            target_id=match.id,
        )
    )

    db.commit()
    db.refresh(match)
    return _to_read(match, db, include_contact=True)


@router.patch("/{match_id}/reject", response_model=MatchRead)
def reject_match(
    match_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.ADMIN)),
):
    match = db.get(MentorMatch, match_id)
    if match is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found.")
    _authorize_reviewer(db, current_user, match)

    if match.status != MatchStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This match has already been reviewed.")

    match.status = MatchStatus.REJECTED
    match.reviewed_by_id = current_user.id
    match.reviewed_at = datetime.now(timezone.utc)
    db.add(
        AuditLog(
            actor_user_id=current_user.id,
            action="match_rejected",
            target_type="mentor_match",
            target_id=match.id,
        )
    )

    db.commit()
    db.refresh(match)
    return _to_read(match, db, include_contact=False)
