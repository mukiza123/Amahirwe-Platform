import os
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# Settings() needs these present to load, even though tests use an
# in-memory SQLite database instead of this placeholder Postgres URL.
os.environ.setdefault("DATABASE_URL", "postgresql://user:password@localhost/amahirwe_test")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")

from app.core.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
import app.api.schools as schools_module  # noqa: E402


@pytest.fixture(autouse=True)
def reset_schools_cache():
    """The schools endpoint caches its result in a process-wide global
    (deliberately — see schools.py), but each test gets a fresh,
    isolated in-memory database via db_session below. Without this, a
    school list cached while test A's database was active would leak
    into test B, which has a completely different database underneath
    it by the time it runs GET /schools."""
    schools_module._schools_cache = None
    yield
    schools_module._schools_cache = None


@pytest.fixture()
def db_session():
    """A SQLAlchemy session bound to a fresh in-memory SQLite database.

    Session-scoped per test (not per-request like the app's own get_db),
    so tests can seed rows (e.g. a School) that the app's own requests
    will then see through the same in-memory database.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()

    def override_get_db():
        try:
            yield session
        finally:
            pass  # closed below, once the test (and its app requests) are done

    app.dependency_overrides[get_db] = override_get_db

    yield session

    session.close()
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    """A TestClient wired to the same in-memory database as db_session.

    Keeps tests fast and independent of a real Postgres instance, while
    exercising the exact same models/queries the app uses in production.
    """
    from fastapi.testclient import TestClient

    with TestClient(app) as test_client:
        yield test_client
