"""
Vercel entry point for the FastAPI backend.

Vercel's Python runtime looks for an ASGI/WSGI app inside files under
/api. This file just re-exports the real app that lives in backend/app,
so the actual application code has no knowledge of being deployed on
Vercel and could be moved to a plain Python host without changes.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.main import app  # noqa: E402,F401
