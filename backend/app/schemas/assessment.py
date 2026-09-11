from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.talent import TalentArea


class ChoiceRead(BaseModel):
    id: str
    text: str


class QuestionRead(BaseModel):
    id: str
    text: str
    choices: list[ChoiceRead]


class AnswerSubmit(BaseModel):
    question_id: str
    choice_id: str


class AssessmentSubmit(BaseModel):
    language: str = Field(default="rw", min_length=2, max_length=2)
    answers: list[AnswerSubmit] = Field(min_length=1)


class TalentResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    talent_area: TalentArea
    score: int
    rank: int
    explanation: str


class AssessmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    student_id: str
    language: str
    completed_at: datetime
    results: list[TalentResultRead]
