from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.talent import TalentArea


class GuardianLinkCreate(BaseModel):
    guardian_email: EmailStr


class GuardianLinkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    student_id: str
    guardian_user_id: str
    guardian_name: str
    guardian_email: str
    created_at: datetime


class ChildTalentSummary(BaseModel):
    talent_area: TalentArea
    score: int
    rank: int
    explanation: str


class ChildRead(BaseModel):
    id: str
    full_name: str
    age_range: str
    school_name: str
    has_completed_assessment: bool
    top_talents: List[ChildTalentSummary]
    mentor_match_status: Optional[str] = None
