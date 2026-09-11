from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.database import get_db
from app.models.student import Student
from app.models.talent import AssessmentAnswer, TalentAssessment, TalentResult
from app.models.user import User, UserRole
from app.schemas.assessment import AssessmentRead, AssessmentSubmit, QuestionRead, TalentResultRead
from app.services.assessment_bank import QUESTION_BANK, talent_area_for_choice
from app.services.talent_scoring import explanation_for, score_answers

router = APIRouter(prefix="/api/assessments", tags=["assessments"])


def _get_student_or_404(db: Session, current_user: User) -> Student:
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complete your student profile before taking the assessment.",
        )
    return student


def _to_assessment_read(assessment: TalentAssessment, results: list[TalentResult]) -> AssessmentRead:
    return AssessmentRead(
        id=assessment.id,
        student_id=assessment.student_id,
        language=assessment.language,
        completed_at=assessment.completed_at,
        results=[
            TalentResultRead(
                talent_area=r.talent_area,
                score=r.score,
                rank=r.rank,
                explanation=explanation_for(r.talent_area),
            )
            for r in results
        ],
    )


@router.get("/questions", response_model=list[QuestionRead])
def list_questions(current_user: User = Depends(require_roles(UserRole.STUDENT))):
    return QUESTION_BANK


@router.post("", response_model=AssessmentRead, status_code=status.HTTP_201_CREATED)
def submit_assessment(
    payload: AssessmentSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
):
    student = _get_student_or_404(db, current_user)

    talent_areas = []
    for answer in payload.answers:
        area = talent_area_for_choice(answer.question_id, answer.choice_id)
        if area is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown question/choice: {answer.question_id}/{answer.choice_id}.",
            )
        talent_areas.append(area)

    assessment = TalentAssessment(student_id=student.id, language=payload.language)
    db.add(assessment)
    db.flush()  # assigns assessment.id without committing yet

    for answer in payload.answers:
        db.add(
            AssessmentAnswer(
                assessment_id=assessment.id,
                question_id=answer.question_id,
                choice_id=answer.choice_id,
            )
        )

    ranked = score_answers(talent_areas)
    results = []
    for entry in ranked:
        result = TalentResult(
            assessment_id=assessment.id,
            student_id=student.id,
            talent_area=entry["talent_area"],
            score=entry["score"],
            rank=entry["rank"],
        )
        db.add(result)
        results.append(result)

    db.commit()
    db.refresh(assessment)
    for result in results:
        db.refresh(result)

    return _to_assessment_read(assessment, results)


@router.get("", response_model=list[AssessmentRead])
def list_my_assessments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
):
    student = _get_student_or_404(db, current_user)
    assessments = (
        db.query(TalentAssessment)
        .filter(TalentAssessment.student_id == student.id)
        .order_by(TalentAssessment.completed_at.desc())
        .all()
    )

    output = []
    for assessment in assessments:
        results = (
            db.query(TalentResult)
            .filter(TalentResult.assessment_id == assessment.id)
            .order_by(TalentResult.rank)
            .all()
        )
        output.append(_to_assessment_read(assessment, results))
    return output


@router.get("/{assessment_id}", response_model=AssessmentRead)
def read_assessment(
    assessment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STUDENT, UserRole.ADMIN)),
):
    assessment = db.get(TalentAssessment, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found.")

    if current_user.role != UserRole.ADMIN:
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        if student is None or assessment.student_id != student.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to do that."
            )

    results = (
        db.query(TalentResult)
        .filter(TalentResult.assessment_id == assessment.id)
        .order_by(TalentResult.rank)
        .all()
    )
    return _to_assessment_read(assessment, results)
