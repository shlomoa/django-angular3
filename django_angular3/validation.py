from __future__ import annotations

from pathlib import Path
from typing import Any

from bin.openui_json import OpenUiJson, OpenUiJsonError
from openapi_spec_validator import validate as validate_openapi_spec
from openapi_spec_validator.validation.exceptions import (
    OpenAPISpecValidatorError,
    OpenAPIValidationError,
)

from .config import ProjectConfig
from .documents import DocumentError, load_document


class ValidationError(ValueError):
    """Raised when validation cannot continue."""


def validate_openapi_document(document: Any) -> list[str]:
    """Return structural validation errors for an in-memory OpenAPI document."""
    errors: list[str] = []
    if not isinstance(document, dict):
        return ["OpenAPI document must be a mapping."]

    if not any(key in document for key in ("openapi", "swagger")):
        errors.append("OpenAPI document must declare either 'openapi' or 'swagger'.")

    paths = document.get("paths")
    if not isinstance(paths, dict):
        errors.append("OpenAPI document must contain a 'paths' mapping.")
        return errors

    if not paths:
        errors.append("OpenAPI document must define at least one path.")
        return errors

    allowed_methods = {
        "get",
        "put",
        "post",
        "delete",
        "options",
        "head",
        "patch",
        "trace",
    }

    for path_name, path_item in paths.items():
        if not isinstance(path_name, str) or not path_name.startswith("/"):
            errors.append(
                f"OpenAPI path '{path_name}' must be a string starting with '/'."
            )
            continue
        if not isinstance(path_item, dict):
            errors.append(f"OpenAPI path '{path_name}' must map to an object.")
            continue

        operations = [name for name in path_item if name in allowed_methods]
        if not operations:
            errors.append(
                f"OpenAPI path '{path_name}' must define at least one HTTP operation."
            )
            continue

        for operation_name in operations:
            operation = path_item[operation_name]
            if not isinstance(operation, dict):
                errors.append(
                    f"Operation '{operation_name}' on path "
                    f"'{path_name}' must be an object."
                )

    return errors


def validate_openui_document(document: Any) -> list[str]:
    """Return OpenUI validation errors from the openui-spec tooling API."""
    try:
        OpenUiJson(document).validate()
    except OpenUiJsonError as exc:
        return str(exc).splitlines()
    return []


def validate_openapi_file(path: str | Path) -> list[str]:
    """Validate an OpenAPI file against the full specification.

    The document is loaded and validated against the OpenAPI specification
    using ``openapi-spec-validator`` for complete OAS compliance checking.
    """
    try:
        document = load_document(path)
    except DocumentError as exc:
        return [str(exc)]

    try:
        validate_openapi_spec(document)
    except (OpenAPISpecValidatorError, OpenAPIValidationError) as exc:
        message = str(exc).strip()
        return [message or f"OpenAPI document failed validation: {exc!r}"]

    return []


def validate_openui_file(path: str | Path) -> list[str]:
    """Load an OpenUI JSON document and return openui-spec validation errors."""
    try:
        document = OpenUiJson.load(path)
        document.validate()
    except OpenUiJsonError as exc:
        return [str(exc)]
    return []


def validate_project_config(config: ProjectConfig) -> list[str]:
    """Return validation errors for all sources and outputs in a project config."""
    errors: list[str] = []

    if not config.openapi_schema.exists():
        errors.append(f"OpenAPI source does not exist: {config.openapi_schema}")
    else:
        errors.extend(validate_openapi_file(config.openapi_schema))

    if not config.openui_specification.exists():
        errors.append(f"OpenUI source does not exist: {config.openui_specification}")
    else:
        errors.extend(validate_openui_file(config.openui_specification))

    if config.angular_workspace.exists() and not config.angular_workspace.is_dir():
        errors.append(
            "Angular output path must be a directory when it exists: "
            f"{config.angular_workspace}"
        )

    return errors
