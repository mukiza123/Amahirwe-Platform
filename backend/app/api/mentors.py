from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.models.mentor import Mentor, MentorExpertise
from app.models.talent import TalentArea
from app.models.user import User, UserRole
from app.schemas.mentor import MentorCreate, MentorRead, MentorUpdate

router = APIRouter(prefix="/api/mentors", tags=["mentors"])


def _to_read(mentor: Mentor, user: User) -> MentorRead:
    return MentorRead(
        id=mentor.id,
        user_id=mentor.user_id,
        bio=mentor.bio,
        district=mentor.district,
        full_name=user.full_name,
        is_verified=user.is_verified,
        expertise_areas=[e.talent_area for e in mentor.expertise],
        created_at=mentor.created_at,
    )


def _get_own_mentor(db: Session, current_user: User) -> Mentor:
    mentor = db.query(Mentor).filter(Mentor.user_id == current_user.id).first()
    if mentor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No mentor profile yet. Complete your profile first.",
        )
    return mentor


@router.post("/me", response_model=MentorRead, status_code=status.HTTP_201_CREATED)
def create_my_profile(
    payload: MentorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.MENTOR)),
):
    existing = db.query(Mentor).filter(Mentor.user_id == current_user.id).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You already have a mentor profile.")

    mentor = Mentor(user_id=current_user.id, bio=payload.bio, district=payload.district)
    db.add(mentor)
    db.flush()
    for area in set(payload.expertise_areas):
        db.add(MentorExpertise(mentor_id=mentor.id, talent_area=area))
    db.commit()
    db.refresh(mentor)
    return _to_read(mentor, current_user)


@router.get("/me", response_model=MentorRead)
def read_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.MENTOR)),
):
    mentor = _get_own_mentor(db, current_user)
    return _to_read(mentor, current_user)


@router.patch("/me", response_model=MentorRead)
def update_my_profile(
    payload: MentorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.MENTOR)),
):
    mentor = _get_own_mentor(db, current_user)

    updates = payload.model_dump(exclude_unset=True, exclude={"expertise_areas"})
    for field, value in updates.items():
        setattr(mentor, field, value)

    if payload.expertise_areas is not None:
        db.query(MentorExpertise).filter(MentorExpertise.mentor_id == mentor.id).delete()
        for area in set(payload.expertise_areas):
            db.add(MentorExpertise(mentor_id=mentor.id, talent_area=area))

    db.commit()
    db.refresh(mentor)
    return _to_read(mentor, current_user)


@router.get("", response_model=List[MentorRead])
def list_mentors(
    talent_area: Optional[TalentArea] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Verified mentors only, since an unverified mentor shouldn't be
    discoverable yet (SRS 5.5)."""

    query = db.query(Mentor).join(User, User.id == Mentor.user_id).filter(User.is_verified.is_(True))
    if talent_area is not None:
        query = query.join(MentorExpertise, MentorExpertise.mentor_id == Mentor.id).filter(
            MentorExpertise.talent_area == talent_area
        )
    mentors = query.order_by(Mentor.created_at.desc()).all()
    return [_to_read(m, m.user) for m in mentors]
