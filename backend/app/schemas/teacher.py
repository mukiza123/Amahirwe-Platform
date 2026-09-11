from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TeacherProfileCreate(BaseModel):
    school_id: str


class TeacherProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    school_id: str
    created_at: datetime


class TeacherStudentCreate(BaseModel):
    """A teacher creating a profile for a student who hasn't registered
    themselves yet (SRS FR-1.2)."""

    full_name: str = Field(min_length=2, max_length=120)
    age_range: str = Field(min_length=2, max_length=10)
    preferred_language: str = Field(default="rw", min_length=2, max_length=2)


class TeacherStudentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: Optional[str]
    school_id: str
    full_name: str
    age_range: str
    preferred_language: str
    created_at: datetime
