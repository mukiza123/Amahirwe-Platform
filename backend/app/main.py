from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
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
