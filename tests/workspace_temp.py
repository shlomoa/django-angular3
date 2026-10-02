"""Repository-local scratch location for tests that write temporary files.

The directory is git-ignored and removed when the test process exits, so a test
run leaves the repository clean.
"""

import atexit
import shutil
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_TEMP_DIR = WORKSPACE_ROOT / "scratch"
WORKSPACE_TEMP_DIR.mkdir(exist_ok=True)
atexit.register(shutil.rmtree, WORKSPACE_TEMP_DIR, ignore_errors=True)
