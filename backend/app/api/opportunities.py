from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.database import get_db
from app.models.opportunity import Opportunity
from app.models.talent import TalentArea
from app.models.user import User, UserRole
from app.schemas.opportunity import OpportunityCreate, OpportunityRead, OpportunityUpdate

router = APIRouter(prefix="/api/opportunities", tags=["opportunities"])


def _to_read(opp: Opportunity) -> OpportunityRead:
    data = OpportunityRead.model_validate(opp)
    data.provider_name = opp.provider.full_name if opp.provider else None
    return data


@router.get("", response_model=List[OpportunityRead])
def list_opportunities(
    talent_area: Optional[TalentArea] = None,
    db: Session = Depends(get_db),
):
    """Public: anyone can browse active opportunities, no login required,
    matching the marketing site's open-access opportunities page."""

    query = db.query(Opportunity).filter(Opportunity.is_active.is_(True))
    if talent_area is not None:
        query = query.filter(Opportunity.talent_area == talent_area)
    opportunities = query.order_by(Opportunity.created_at.desc()).all()
    return [_to_read(o) for o in opportunities]


@router.get("/mine", response_model=List[OpportunityRead])
def list_my_opportunities(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.PROVIDER)),
):
    opportunities = (
        db.query(Opportunity)
        .filter(Opportunity.provider_id == current_user.id)
        .order_by(Opportunity.created_at.desc())
        .all()
    )
    return [_to_read(o) for o in opportunities]


@router.post("", response_model=OpportunityRead, status_code=status.HTTP_201_CREATED)
def create_opportunity(
    payload: OpportunityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.PROVIDER)),
):
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your provider account must be verified by an administrator before you can post opportunities.",
        )

    opportunity = Opportunity(provider_id=current_user.id, **payload.model_dump())
    db.add(opportunity)
    db.commit()
    db.refresh(opportunity)
    return _to_read(opportunity)


def _get_own_opportunity(db: Session, current_user: User, opportunity_id: str) -> Opportunity:
    opportunity = db.get(Opportunity, opportunity_id)
    if opportunity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found.")
    if opportunity.provider_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to do that.")
    return opportunity


@router.patch("/{opportunity_id}", response_model=OpportunityRead)
def update_opportunity(
    opportunity_id: str,
    payload: OpportunityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.PROVIDER)),
):
    opportunity = _get_own_opportunity(db, current_user, opportunity_id)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(opportunity, field, value)
    db.commit()
    db.refresh(opportunity)
    return _to_read(opportunity)


@router.delete("/{opportunity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_opportunity(
    opportunity_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.PROVIDER)),
):
    opportunity = _get_own_opportunity(db, current_user, opportunity_id)
    db.delete(opportunity)
    db.commit()
