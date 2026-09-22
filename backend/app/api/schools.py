import time
from typing import List, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.school import School
from app.models.user import User
from app.schemas.school import SchoolCreate, SchoolRead

router = APIRouter(prefix="/api/schools", tags=["schools"])

# Every student/teacher profile form re-fetches this list, but the
# school directory is public reference data that essentially never
# changes at runtime — no need to hit Postgres for it on every single
# request. A small in-process TTL cache (no Redis: this is one
# uvicorn process, and the data isn't user-specific or sensitive)
# avoids a full round trip to Neon for a query result that's the same
# every time within the window.
_SCHOOLS_CACHE_TTL_SECONDS = 300
_schools_cache: Optional[List[SchoolRead]] = None
_schools_cache_expires_at: float = 0.0


@router.get("", response_model=List[SchoolRead])
def list_schools(db: Session = Depends(get_db)):
    """Public: needed to populate the school picker on the student and
    teacher profile-completion forms. Only approved schools are listed
    here — a school someone just self-submitted isn't usable by anyone
    else until an admin reviews it (see POST below)."""

    global _schools_cache, _schools_cache_expires_at

    now = time.monotonic()
    if _schools_cache is None or now >= _schools_cache_expires_at:
        rows = db.query(School).filter(School.is_approved.is_(True)).order_by(School.name).all()
        _schools_cache = [SchoolRead.model_validate(row) for row in rows]
        _schools_cache_expires_at = now + _SCHOOLS_CACHE_TTL_SECONDS

    return _schools_cache


def invalidate_schools_cache() -> None:
    """Called wherever approval status changes (see admin.approve_school)
    so a newly-approved school shows up immediately instead of waiting
    out the TTL above."""
    global _schools_cache
    _schools_cache = None


@router.post("", response_model=SchoolRead, status_code=status.HTTP_201_CREATED)
def request_school(
    payload: SchoolCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """For a student/teacher whose school isn't in the picker yet. The
    new row starts unapproved and isn't returned by GET /schools for
    anyone else, but the caller can attach their own profile to it
    immediately (its id is returned right here) rather than being
    blocked until an admin reviews it."""

    existing = (
        db.query(School)
        .filter(School.name.ilike(payload.name.strip()), School.district.ilike(payload.district.strip()))
        .first()
    )
    if existing is not None:
        return existing

    school = School(
        name=payload.name.strip(),
        district=payload.district.strip(),
        province=payload.province.strip(),
        is_approved=False,
        requested_by_user_id=current_user.id,
    )
    db.add(school)
    db.commit()
    db.refresh(school)
    return school
