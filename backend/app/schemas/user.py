from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole

# Administrator accounts are seeded by the platform, not self-registered,
# so registration only accepts the roles a person can sign themselves up as.
RegisterableRole = Literal["student", "teacher", "mentor", "provider", "parent"]


class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: RegisterableRole


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class EmailVerificationCode(BaseModel):
    code: str = Field(min_length=6, max_length=6)


class GoogleAuth(BaseModel):
    # The ID token Google's Identity Services library hands back to the
    # frontend after the user picks an account; role is only needed the
    # first time a brand-new email signs in this way (see /auth/google).
    id_token: str
    role: Optional[RegisterableRole] = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str
    email: EmailStr
    role: UserRole
    is_verified: bool
    email_verified: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
    # Stands in for actually emailing the code: there's no email-sending
    # service configured for this prototype, so the code a real email
    # would contain is returned directly here instead, only on
    # register/resend. Replace with a real email send + drop this field
    # once the app has a mail provider.
    dev_verification_code: Optional[str] = None


class GoogleAuthResult(BaseModel):
    """A brand-new Google sign-in with no matching account can't be
    turned into a Token yet — there's no role to put on the user row.
    needs_role=True means the frontend should collect one and call
    /auth/google again with the same id_token before this becomes a
    normal Token response."""

    needs_role: bool = False
    access_token: Optional[str] = None
    token_type: str = "bearer"
    user: Optional[UserRead] = None
