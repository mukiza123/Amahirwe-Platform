from typing import Dict, List, Optional

from pydantic import BaseModel

from app.models.talent import TalentArea


class StudentSummary(BaseModel):
    id: str
    full_name: str
    age_range: str
    is_registered: bool
    top_talent_area: Optional[TalentArea] = None
    top_score: Optional[int] = None


class TeacherOverview(BaseModel):
    student_count: int
    pending_match_count: int
    students_with_assessment_count: int
    students: List[StudentSummary]


class MentorOverview(BaseModel):
    expertise_count: int
    approved_mentee_count: int
    pending_request_count: int
    rejected_count: int


class OpportunityOverview(BaseModel):
    total_count: int
    active_count: int
    by_talent_area: Dict[str, int]


class DailyCount(BaseModel):
    date: str
    count: int


class AdminOverview(BaseModel):
    total_users: int
    users_by_role: Dict[str, int]
    active_student_count: int
    active_mentor_count: int
    active_opportunity_count: int
    pending_verification_count: int
    signups_last_14_days: List[DailyCount]
    talent_area_distribution: Dict[str, int]
