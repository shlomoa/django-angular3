from __future__ import annotations

import json
import tomllib
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - exercised when optional dep absent
    yaml = None


class DocumentError(ValueError):
    """Raised when a structured input document cannot be loaded."""


def load_document(path: str | Path) -> Any:
    file_path = Path(path)
    if not file_path.exists():
        raise DocumentError(f"Document does not exist: {file_path}")

    suffix = file_path.suffix.lower()
    text = file_path.read_text(encoding="utf-8")

    if suffix == ".json":
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise DocumentError(f"Invalid JSON in {file_path}: {exc}") from exc

    if suffix == ".toml":
        try:
            return tomllib.loads(text)
        except tomllib.TOMLDecodeError as exc:
            raise DocumentError(f"Invalid TOML in {file_path}: {exc}") from exc

    if suffix in {".yaml", ".yml"}:
        if yaml is None:
            raise DocumentError(
                "YAML support requires the optional 'yaml' extra. "
                "Install with `pip install -e .[yaml]` or use JSON/TOML."
            )
        try:
            return yaml.safe_load(text)
        except yaml.YAMLError as exc:
            raise DocumentError(f"Invalid YAML in {file_path}: {exc}") from exc

    raise DocumentError(
        f"Unsupported document format for {file_path}. "
        "Use .json, .toml, .yaml, or .yml."
    )
