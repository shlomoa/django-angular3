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
    openapi_source: Path
    ui_source: Path
    angular_output: Path
    openapi_generator_config: Path | None = None
    ng_openapi_gen_config: Path | None = None


def load_project_config(path: str | Path) -> ProjectConfig:
    config_path = Path(path).resolve()
    try:
        document = load_document(config_path)
    except DocumentError as exc:
        raise ConfigError(str(exc)) from exc

    if not isinstance(document, dict):
        raise ConfigError("Project configuration must be a mapping.")

    project = _require_mapping(document, "project")
    openapi = _require_mapping(document, "openapi")
    ui = _require_mapping(document, "ui")
    angular = _require_mapping(document, "angular")

    root = config_path.parent
    project_name = _require_string(project, "name", section="project")
    openapi_source = _resolve_path(root, _require_string(openapi, "source", section="openapi"))
    ui_source = _resolve_path(root, _require_string(ui, "source", section="ui"))
    angular_output_value = angular.get("output", angular.get("package"))
    if not isinstance(angular_output_value, str) or not angular_output_value.strip():
        raise ConfigError("Configuration value 'angular.output' must be a non-empty string.")
    angular_output = _resolve_path(root, angular_output_value)

    openapi_generator_config = _optional_path(
        root, openapi.get("openapiGeneratorConfig"), "openapi.openapiGeneratorConfig"
    )
    ng_openapi_gen_config = _optional_path(
        root, openapi.get("ngOpenApiGenConfig"), "openapi.ngOpenApiGenConfig"
    )

    return ProjectConfig(
        config_path=config_path,
        project_name=project_name,
        openapi_source=openapi_source,
        ui_source=ui_source,
        angular_output=angular_output,
        openapi_generator_config=openapi_generator_config,
        ng_openapi_gen_config=ng_openapi_gen_config,
    )


def _require_mapping(document: dict[str, Any], key: str) -> dict[str, Any]:
    value = document.get(key)
    if not isinstance(value, dict):
        raise ConfigError(f"Configuration section '{key}' must be a mapping.")
    return value


def _require_string(document: dict[str, Any], key: str, *, section: str) -> str:
    value = document.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"Configuration value '{section}.{key}' must be a non-empty string.")
    return value


def _resolve_path(root: Path, raw_path: str) -> Path:
    return (root / raw_path).resolve()


def _optional_path(root: Path, value: Any, label: str) -> Path | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"Configuration value '{label}' must be a non-empty string.")
    return (root / value).resolve()
