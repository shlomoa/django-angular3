from __future__ import annotations

import shutil
from collections.abc import Iterable
from pathlib import Path


def project_root() -> Path:
    """Return the directory from which the cleanup command was invoked."""
    return Path.cwd()


def clean_artifact_paths(root: Path) -> Iterable[Path]:
    """Yield generated build and package artifacts below ``root``."""
    for relative_path in (
        ".eggs",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "build",
        "dist",
        "docs/_build",
    ):
        path = root / relative_path
        if path.exists() or path.is_symlink():
            yield path

    yield from root.glob("*.egg-info")
    yield from root.rglob("__pycache__")


def remove_artifacts(paths: Iterable[Path]) -> list[Path]:
    """Remove artifact paths and return the paths that were removed."""
    removed: list[Path] = []
    for path in paths:
        if path.is_symlink() or path.is_file():
            path.unlink()
        else:
            shutil.rmtree(path)
        removed.append(path)
    return removed
