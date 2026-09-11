from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class StudentCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    school_id: str
    age_range: str = Field(min_length=2, max_length=10)
    preferred_language: str = Field(default="rw", min_length=2, max_length=2)


class StudentUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    age_range: Optional[str] = Field(default=None, min_length=2, max_length=10)
    preferred_language: Optional[str] = Field(default=None, min_length=2, max_length=2)


class StudentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: Optional[str]
    school_id: str
    full_name: str
    age_range: str
    preferred_language: str
    created_at: datetime
