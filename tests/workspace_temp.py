"""Scratch location for tests that write temporary files.

The directory lives under the operating system's temporary directory and is
removed when the test process exits, so a test run leaves the repository clean.
"""

import atexit
import shutil
import tempfile
from pathlib import Path

WORKSPACE_TEMP_DIR = Path(tempfile.mkdtemp(prefix="django-angular3-tests-"))
FIXTURE_BUILD_DIR = Path(__file__).resolve().parent / "fixtures" / "build"

atexit.register(shutil.rmtree, WORKSPACE_TEMP_DIR, ignore_errors=True)
atexit.register(shutil.rmtree, FIXTURE_BUILD_DIR, ignore_errors=True)
