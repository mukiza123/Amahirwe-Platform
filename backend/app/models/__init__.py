from app.core.database import Base

# As each phase adds a model (Teacher, Mentor, ...), import it here so
# Alembic's autogenerate can see it via Base.metadata.
from app.models.user import User, UserRole  # noqa: E402,F401
from app.models.school import School  # noqa: E402,F401
from app.models.student import Student  # noqa: E402,F401
from app.models.talent import (  # noqa: E402,F401
    AssessmentAnswer,
    TalentArea,
    TalentAssessment,
    TalentResult,
)
from app.models.teacher import TeacherProfile  # noqa: E402,F401
from app.models.mentor import Mentor, MentorExpertise, MentorMatch, MatchStatus  # noqa: E402,F401
from app.models.opportunity import Opportunity  # noqa: E402,F401
from app.models.audit import AuditLog, Notification  # noqa: E402,F401
from app.models.guardian import StudentGuardian  # noqa: E402,F401
