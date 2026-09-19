import enum
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserRole(str, enum.Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    MENTOR = "mentor"
    PROVIDER = "provider"
    ADMIN = "admin"
    PARENT = "parent"


class User(Base):
    """The single account table every role authenticates through.

    Role-specific details (e.g. a student's school, a mentor's expertise)
    live in their own tables added in later phases, linked back to this
    User by foreign key; this table only ever holds login/identity data.
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", values_callable=lambda cls: [e.value for e in cls]),
        nullable=False,
    )

    # Mentors and opportunity providers must be verified by an administrator
    # before they can appear in matches or publish opportunities (SRS 5.5).
    # Other roles are considered verified as soon as they register.
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # A self-registered account must confirm ownership of its email
    # address with a one-time code before it can use the app (separate
    # from is_verified above, which is an admin credential check for
    # mentors/providers, not identity/email ownership).
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_verification_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    email_verification_code_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Wrong guesses against the current code; the code is invalidated
    # once this hits a limit, so a stolen/guessed-at token can't be
    # brute-forced indefinitely (see MAX_VERIFICATION_ATTEMPTS in auth.py).
    email_verification_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Throttles /me/resend-verification so a user (or a script with a
    # stolen session) can't spam new codes.
    email_verification_last_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Forgot-password: same one-time-code pattern as email verification,
    # but tracked separately since a reset can happen on an already
    # email_verified account and shouldn't disturb that state.
    password_reset_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    password_reset_code_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    password_reset_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    password_reset_last_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
