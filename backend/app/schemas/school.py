from pydantic import BaseModel, ConfigDict


class SchoolRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    district: str
    province: str
