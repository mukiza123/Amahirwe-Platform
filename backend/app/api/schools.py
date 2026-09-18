import time
from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.school import School
from app.schemas.school import SchoolRead

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
    teacher profile-completion forms."""

    global _schools_cache, _schools_cache_expires_at

    now = time.monotonic()
    if _schools_cache is None or now >= _schools_cache_expires_at:
        rows = db.query(School).order_by(School.name).all()
        _schools_cache = [SchoolRead.model_validate(row) for row in rows]
        _schools_cache_expires_at = now + _SCHOOLS_CACHE_TTL_SECONDS

    return _schools_cache
