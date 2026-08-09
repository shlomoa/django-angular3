"""Repository-local scratch location for tests that write temporary files."""

from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_TEMP_DIR = WORKSPACE_ROOT / "tmparea"
WORKSPACE_TEMP_DIR.mkdir(exist_ok=True)
