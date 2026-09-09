from app.core.database import Base

# As each phase adds a model (User, Student, Teacher, Mentor, ...), import it
# here so Alembic's autogenerate can see it via Base.metadata.
