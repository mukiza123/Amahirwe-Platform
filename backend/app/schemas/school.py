from pydantic import BaseModel, ConfigDict, Field


class SchoolRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    district: str
    province: str
    is_approved: bool


class SchoolCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    district: str = Field(min_length=2, max_length=120)
    province: str = Field(min_length=2, max_length=120)
