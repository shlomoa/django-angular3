"""A fingerprint of the Django migrations an OpenAPI schema was exported against.

File times do not survive a checkout or a copy, so freshness of the schema is not
judged from them. ``openapi_schema_export`` records the fingerprint of the migrations
beside the schema (``<schema stem>.migrations.json``); the ``pre-construction`` Hook
compares the recorded fingerprint with the current one. A schema with no record, as a
committed schema that was never exported here, cannot be judged and is not blocked.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Final

IGNORED_DIRECTORIES: Final = frozenset(
    {"node_modules", ".git", ".venv", "venv", "build", "dist", "__pycache__"}
)


def migration_modules(root: Path) -> list[Path]:
    """Every migration module below ``root`` (``*/migrations/*.py``), sorted."""
    modules: list[Path] = []
    for path in sorted(root.rglob("migrations/*.py")):
        relative = path.relative_to(root)
        if path.name == "__init__.py" or any(
            part in IGNORED_DIRECTORIES for part in relative.parts
        ):
            continue
        modules.append(path)
    return modules


def migrations_fingerprint(root: Path) -> str:
    """SHA-256 over the relative path and content of every migration module."""
    digest = hashlib.sha256()
    for path in migration_modules(root):
        digest.update(path.relative_to(root).as_posix().encode("utf-8") + b"\0")
        digest.update(path.read_bytes() + b"\0")
    return digest.hexdigest()


def record_path(schema: Path) -> Path:
    """Where the fingerprint of a schema is recorded: ``<stem>.migrations.json``."""
    return schema.with_name(f"{schema.stem}.migrations.json")


def write_record(schema: Path, root: Path) -> None:
    record_path(schema).write_text(
        json.dumps({"migrations": migrations_fingerprint(root)}, indent=2) + "\n",
        encoding="utf-8",
    )


def read_record(schema: Path) -> str | None:
    """The recorded fingerprint, or ``None`` when there is no usable record."""
    try:
        document: Any = json.loads(record_path(schema).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    value = document.get("migrations") if isinstance(document, dict) else None
    return value if isinstance(value, str) else None
