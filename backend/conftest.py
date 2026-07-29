"""
pytest conftest for the DeceptiScan backend test suite.

Adds backend/ to sys.path so that `import services.ml_service` works
regardless of whether pytest is run from the repo root or from backend/.
"""
import sys
from pathlib import Path

# Insert D:\pylibs and backend/ at the front of sys.path
_PYLIBS = r"D:\pylibs"
if _PYLIBS in sys.path:
    sys.path.remove(_PYLIBS)
sys.path.insert(0, _PYLIBS)

backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(1, str(backend_dir))
