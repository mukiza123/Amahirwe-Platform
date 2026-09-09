import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# Tests never touch a real database, so these just need to be present for
# Settings() to load without reading backend/.env.
os.environ.setdefault("DATABASE_URL", "postgresql://user:password@localhost/amahirwe_test")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
