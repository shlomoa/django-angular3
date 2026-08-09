from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .documents import DocumentError, load_document


class ConfigError(ValueError):
    """Raised when the project configuration is invalid."""


@dataclass(frozen=True)
class ProjectConfig:
    config_path: Path
    project_name: str
    openapi_schema: Path
    openui_specification: Path
    angular_workspace: Path


PROJECT_CONFIG_FILENAME = "django-angular3-project.json"


def discover_project_config_path() -> Path:
    """Return the canonical project configuration path for this runtime."""
    try:
        from django.conf import settings as django_settings
        from django.core.exceptions import ImproperlyConfigured

        if getattr(django_settings, "configured", False):
            return Path(django_settings.BASE_DIR).resolve() / PROJECT_CONFIG_FILENAME
    except (ImportError, ImproperlyConfigured, AttributeError):
        pass
    return Path.cwd().resolve() / PROJECT_CONFIG_FILENAME


def load_project_config(path: str | Path | None = None) -> ProjectConfig:
    """Load project configuration.

    ``path`` remains available for callers that supply a project configuration
    explicitly. When omitted, the canonical project file is discovered.
    """
    config_path = Path(path or discover_project_config_path()).resolve()
    try:
        document: dict[str, Any] | None = load_document(config_path)
    except DocumentError as exc:
        raise ConfigError(str(exc)) from exc

    if not isinstance(document, dict):
        raise ConfigError("Project configuration must be a mapping.")

    legacy_fields = {"openapi", "openui", "angular"} & document.keys()
    if legacy_fields:
        labels = ", ".join(sorted(legacy_fields))
        raise ConfigError(
            "Legacy project configuration field(s) are not supported: "
            f"{labels}. Use the 'artifacts' mapping."
        )
    return _load_project_configuration(document, config_path)


def _load_project_configuration(
    document: dict[str, Any], config_path: Path
) -> ProjectConfig:
    project: dict[str, Any] = _require_mapping(document, "project")
    artifacts: dict[str, Any] = _require_mapping(document, "artifacts")
    root = config_path.parent

    return ProjectConfig(
        config_path=config_path,
        project_name=_require_string(project, "name", section="project"),
        openapi_schema=_resolve_path(
            root, _require_string(artifacts, "openapiSchema", section="artifacts")
        ),
        openui_specification=_resolve_path(
            root,
            _require_string(artifacts, "openuiSpecification", section="artifacts"),
        ),
        angular_workspace=_resolve_path(
            root,
            _require_string(artifacts, "angularWorkspace", section="artifacts"),
        ),
    )


def _require_mapping(document: dict[str, Any], key: str) -> dict[str, Any]:
    value: dict[str, Any] | None = document.get(key)
    if not isinstance(value, dict):
        raise ConfigError(f"Configuration section '{key}' must be a mapping.")
    return value


def _require_string(document: dict[str, Any], key: str, *, section: str) -> str:
    value = document.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(
            f"Configuration value '{section}.{key}' must be a non-empty string."
        )
    return value


def _resolve_path(root: Path, raw_path: str) -> Path:
    return (root / raw_path).resolve()


def get_previous_schema_path(source: Path) -> Path:
    """Return the conventional path for the previous schema artifact.

    The previous schema is stored alongside the current schema with
    ``.previous`` inserted before the file extension.  For example::

        spec/openapi/source/api.json  →  spec/openapi/source/api.previous.json

    This path is written by ``export_schema`` before the current schema is
    overwritten, and consumed by ``build_app`` for change detection.
    """
    return source.parent / (source.stem + ".previous" + source.suffix)
