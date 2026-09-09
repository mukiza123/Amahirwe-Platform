from app.core.database import Base

# As each phase adds a model (Student, Teacher, Mentor, ...), import it here
# so Alembic's autogenerate can see it via Base.metadata.
from app.models.user import User, UserRole  # noqa: E402,F401
