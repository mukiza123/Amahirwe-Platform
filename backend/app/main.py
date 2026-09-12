from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.admin import router as admin_router
from app.api.assessments import router as assessments_router
from app.api.auth import router as auth_router
from app.api.matches import router as matches_router
from app.api.mentors import router as mentors_router
from app.api.notifications import router as notifications_router
from app.api.opportunities import router as opportunities_router
from app.api.parents import router as parents_router
from app.api.schools import router as schools_router
from app.api.students import router as students_router
from app.api.teachers import router as teachers_router
from app.core.config import settings

app = FastAPI(
    title="Amahirwe API",
    description="Backend API for Amahirwe: Discover, Connect, Grow.",
    version="0.1.0",
)

if settings.cors_origins == "*":
    origins = ["*"]
else:
    origins = [origin.strip() for origin in settings.cors_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    """Simple endpoint used to confirm the API and DB config are wired up."""
    return {"status": "ok", "service": "Amahirwe API"}


app.include_router(auth_router)
app.include_router(schools_router)
app.include_router(students_router)
app.include_router(assessments_router)
app.include_router(teachers_router)
app.include_router(mentors_router)
app.include_router(matches_router)
app.include_router(opportunities_router)
app.include_router(admin_router)
app.include_router(notifications_router)
app.include_router(parents_router)
