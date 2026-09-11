from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.database import get_db
from app.models.audit import AuditLog, Notification
from app.models.user import User, UserRole
from app.schemas.admin import AdminUserRead, AuditLogRead

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


@router.get("/audit-log", response_model=List[AuditLogRead])
def list_audit_log(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    return db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(200).all()
