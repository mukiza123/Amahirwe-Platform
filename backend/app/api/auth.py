import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User, UserRole
from app.schemas.user import (
    EmailVerificationCode,
    GoogleAuth,
    GoogleAuthResult,
    PasswordChange,
    Token,
    UserCreate,
    UserLogin,
    UserRead,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

# One shared Request object for Google's token-verification HTTP calls
# (it fetches Google's public signing keys, cached internally), rather
# than building a new one per request.
_google_auth_request = google_requests.Request()

# Mentors and opportunity providers need admin verification before they're
# visible in matches/opportunities (SRS 5.5); everyone else is usable right away.
ROLES_REQUIRING_VERIFICATION = {UserRole.MENTOR, UserRole.PROVIDER}

EMAIL_VERIFICATION_CODE_TTL_MINUTES = 15


def _issue_verification_code(user: User) -> str:
    """Generates a fresh 6-digit code and stores it (with an expiry) on
    the user. Caller is responsible for committing. secrets, not
    random, because this guards account access even though a 6-digit
    space is small regardless — no reason to use a weaker generator."""
    code = f"{secrets.randbelow(1_000_000):06d}"
    user.email_verification_code = code
    user.email_verification_code_expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=EMAIL_VERIFICATION_CODE_TTL_MINUTES
    )
    return code


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    role = UserRole(payload.role)

    user = User(
        full_name=payload.full_name.strip(),
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        role=role,
        is_verified=role not in ROLES_REQUIRING_VERIFICATION,
    )
    code = _issue_verification_code(user)

    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists.")
    db.refresh(user)

    token = create_access_token(subject=user.id, extra_claims={"role": user.role.value})
    return Token(access_token=token, user=UserRead.model_validate(user), dev_verification_code=code)


@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()

    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password.")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account has been deactivated.")

    token = create_access_token(subject=user.id, extra_claims={"role": user.role.value})
    return Token(access_token=token, user=UserRead.model_validate(user))


@router.post("/google", response_model=GoogleAuthResult)
def google_auth(payload: GoogleAuth, db: Session = Depends(get_db)):
    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google sign-in isn't configured on this server.",
        )

    try:
        claims = google_id_token.verify_oauth2_token(
            payload.id_token, _google_auth_request, settings.google_client_id
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Google sign-in failed. Please try again."
        )

    email = (claims.get("email") or "").lower()
    if not email or not claims.get("email_verified"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Your Google account's email isn't verified."
        )

    user = db.query(User).filter(User.email == email).first()

    if user is None:
        if payload.role is None:
            # First time we've seen this email and don't know what role
            # to give it yet — the frontend collects one and calls back
            # with the same id_token, which verifies fine again since
            # this endpoint has no side effects until a role is known.
            return GoogleAuthResult(needs_role=True)

        role = UserRole(payload.role)
        user = User(
            full_name=(claims.get("name") or email.split("@")[0]).strip(),
            email=email,
            # Google-only accounts have no password to check, but the
            # column is NOT NULL; a random value the user will never
            # know keeps password login correctly failing for them
            # rather than needing a schema change for a nullable column.
            hashed_password=hash_password(secrets.token_urlsafe(32)),
            role=role,
            is_verified=role not in ROLES_REQUIRING_VERIFICATION,
            email_verified=True,
        )
        db.add(user)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists."
            )
        db.refresh(user)
    elif not user.email_verified:
        # Google just proved they own this inbox, which satisfies the
        # same thing the code-based flow was checking.
        user.email_verified = True
        db.commit()
        db.refresh(user)

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account has been deactivated.")

    token = create_access_token(subject=user.id, extra_claims={"role": user.role.value})
    return GoogleAuthResult(access_token=token, user=UserRead.model_validate(user))


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/me/verify-email", response_model=UserRead)
def verify_email(
    payload: EmailVerificationCode,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.email_verified:
        return current_user

    now = datetime.now(timezone.utc)
    expires_at = current_user.email_verification_code_expires_at
    # Postgres (production) always returns this tz-aware, since the
    # column is DateTime(timezone=True) — but SQLite (used in tests)
    # drops tzinfo on read, so a naive value here is assumed to already
    # be UTC, matching how it was stored, rather than raising.
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    code_matches = current_user.email_verification_code is not None and secrets.compare_digest(
        current_user.email_verification_code, payload.code
    )
    not_expired = expires_at is not None and expires_at > now
    if not (code_matches and not_expired):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="That code is incorrect or has expired.")

    current_user.email_verified = True
    current_user.email_verification_code = None
    current_user.email_verification_code_expires_at = None
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/resend-verification", response_model=Token)
def resend_verification(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.email_verified:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This account is already verified.")

    code = _issue_verification_code(current_user)
    db.commit()
    db.refresh(current_user)

    token = create_access_token(subject=current_user.id, extra_claims={"role": current_user.role.value})
    return Token(access_token=token, user=UserRead.model_validate(current_user), dev_verification_code=code)


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect.")

    current_user.hashed_password = hash_password(payload.new_password)
    db.commit()
