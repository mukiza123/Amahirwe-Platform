from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.talent import TalentArea


class OpportunityCreate(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    description: str = Field(min_length=10, max_length=4000)
    talent_area: Optional[TalentArea] = None
    location: str = Field(min_length=2, max_length=160)
    deadline: Optional[date] = None


class OpportunityUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=160)
    description: Optional[str] = Field(default=None, min_length=10, max_length=4000)
    talent_area: Optional[TalentArea] = None
    location: Optional[str] = Field(default=None, min_length=2, max_length=160)
    deadline: Optional[date] = None
    is_active: Optional[bool] = None


class OpportunityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    provider_id: str
    title: str
    description: str
    talent_area: Optional[TalentArea]
    location: str
    deadline: Optional[date]
    is_active: bool
    created_at: datetime
    provider_name: Optional[str] = None
