from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.school import School
from app.schemas.school import SchoolRead

router = APIRouter(prefix="/api/schools", tags=["schools"])


@router.get("", response_model=List[SchoolRead])
def list_schools(db: Session = Depends(get_db)):
    """Public: needed to populate the school picker on the student and
    teacher profile-completion forms."""

    return db.query(School).order_by(School.name).all()
