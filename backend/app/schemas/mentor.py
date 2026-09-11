from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.talent import TalentArea
from app.models.mentor import MatchStatus


class MentorCreate(BaseModel):
    bio: Optional[str] = Field(default=None, max_length=2000)
    district: str = Field(min_length=2, max_length=120)
    expertise_areas: List[TalentArea] = Field(min_length=1, max_length=7)


class MentorUpdate(BaseModel):
    bio: Optional[str] = Field(default=None, max_length=2000)
    district: Optional[str] = Field(default=None, min_length=2, max_length=120)
    expertise_areas: Optional[List[TalentArea]] = Field(default=None, min_length=1, max_length=7)


class MentorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    bio: Optional[str]
    district: str
    full_name: str
    is_verified: bool
    expertise_areas: List[TalentArea]
    created_at: datetime


class MatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    student_id: str
    mentor_id: str
    talent_area: TalentArea
    status: MatchStatus
    reviewed_at: Optional[datetime]
    created_at: datetime

    # Only populated once status is APPROVED, and only for the student or
    # mentor in the match (SRS 5.5: no contact before approval).
    student_name: Optional[str] = None
    student_contact_email: Optional[str] = None
    mentor_name: Optional[str] = None
    mentor_contact_email: Optional[str] = None
