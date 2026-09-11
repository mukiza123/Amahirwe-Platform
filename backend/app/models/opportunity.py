import enum
import uuid
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.talent import TalentArea


class Opportunity(Base):
    """A scholarship, competition, workshop or program posted by a
    verified provider (SRS 5.6). talent_area is optional since some
    opportunities are open to every talent area."""

    __tablename__ = "opportunities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    talent_area: Mapped[Optional[TalentArea]] = mapped_column(
        Enum(TalentArea, name="talent_area", values_callable=lambda cls: [e.value for e in cls]),
        nullable=True,
    )
    location: Mapped[str] = mapped_column(String(160), nullable=False)
    deadline: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    provider: Mapped["User"] = relationship("User", lazy="joined", viewonly=True)  # noqa: F821
