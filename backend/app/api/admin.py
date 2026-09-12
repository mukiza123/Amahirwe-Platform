from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.database import get_db
from app.models.audit import AuditLog, Notification
from app.models.mentor import Mentor
from app.models.opportunity import Opportunity
from app.models.student import Student
from app.models.talent import TalentResult
from app.models.user import User, UserRole
from app.schemas.admin import AdminUserRead, AuditLogRead
from app.schemas.stats import AdminOverview, DailyCount

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/users", response_model=List[AdminUserRead])
def list_users(
    role: Optional[UserRole] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    query = db.query(User)
    if role is not None:
        query = query.filter(User.role == role)
    return query.order_by(User.created_at.desc()).all()


@router.patch("/users/{user_id}/verify", response_model=AdminUserRead)
def verify_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Verifies a mentor or opportunity provider (SRS 5.5/5.6): only
    after this can they appear in matches or publish opportunities."""

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    user.is_verified = True
    db.add(AuditLog(actor_user_id=current_user.id, action="user_verified", target_type="user", target_id=user.id))
    db.add(Notification(user_id=user.id, message="Your account has been verified by an administrator."))
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}/deactivate", response_model=AdminUserRead)
def deactivate_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    if user.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You can't deactivate your own account.")

    user.is_active = False
    db.add(AuditLog(actor_user_id=current_user.id, action="user_deactivated", target_type="user", target_id=user.id))
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}/activate", response_model=AdminUserRead)
def activate_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    user.is_active = True
    db.add(AuditLog(actor_user_id=current_user.id, action="user_activated", target_type="user", target_id=user.id))
    db.commit()
    db.refresh(user)
    return user


@router.get("/overview", response_model=AdminOverview)
def read_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Real, computed platform numbers for the admin Home dashboard.
    Nothing here is simulated; every figure is a direct query result."""

    users = db.query(User).all()
    users_by_role = Counter(u.role.value for u in users)

    pending_verification_count = sum(
        1 for u in users if u.role in (UserRole.MENTOR, UserRole.PROVIDER) and not u.is_verified
    )

    cutoff = datetime.now(timezone.utc) - timedelta(days=13)
    by_day = Counter()
    for u in users:
        created = u.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        if created >= cutoff:
            by_day[created.date().isoformat()] += 1

    signups = []
    for offset in range(13, -1, -1):
        day = (datetime.now(timezone.utc) - timedelta(days=offset)).date().isoformat()
        signups.append(DailyCount(date=day, count=by_day.get(day, 0)))

    top_results = db.query(TalentResult).filter(TalentResult.rank == 1).all()
    talent_distribution = Counter(r.talent_area.value for r in top_results)

    return AdminOverview(
        total_users=len(users),
        users_by_role=dict(users_by_role),
        active_student_count=db.query(Student).count(),
        active_mentor_count=db.query(Mentor).join(User, User.id == Mentor.user_id).filter(User.is_verified.is_(True)).count(),
        active_opportunity_count=db.query(Opportunity).filter(Opportunity.is_active.is_(True)).count(),
        pending_verification_count=pending_verification_count,
        signups_last_14_days=signups,
        talent_area_distribution=dict(talent_distribution),
    )


@router.get("/audit-log", response_model=List[AuditLogRead])
def list_audit_log(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    return db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(200).all()
