"""
pytest conftest for the DeceptiScan backend test suite.

Adds backend/ to sys.path so that `import services.ml_service` works
regardless of whether pytest is run from the repo root or from backend/.
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
import os
from urllib.parse import urlparse

@pytest.fixture(scope="session", autouse=True)
def log_db_connection():
    db_url = os.getenv("DATABASE_URL", "")
    if db_url:
        parsed = urlparse(db_url)
        safe_url = f"{parsed.scheme}://{parsed.username}:****@{parsed.hostname}:{parsed.port or 5432}{parsed.path}"
        print(f"\n[DeceptiScan Test Suite] Connected to database: {safe_url}")
    else:
        print("\n[DeceptiScan Test Suite] No DATABASE_URL set.")

