from __future__ import annotations

import subprocess
import warnings
from pathlib import Path
from typing import Any

from bin.openui_json import OpenUiJson, OpenUiJsonError

from .config import ProjectConfig
from .documents import DocumentError, load_document
from .tools import find_speakeasy_openapi


class ValidationError(ValueError):
    """Raised when validation cannot continue."""


def _run_speakeasy_validate(path: str | Path) -> list[str]:
    """Run ``openapi spec validate`` against *path*.

    Returns a list of error strings (empty if valid).
    Raises ``RuntimeError`` if the binary cannot be found.
    """
    binary = find_speakeasy_openapi()
    if binary is None:
        raise RuntimeError(
            "Speakeasy OpenAPI CLI ('openapi') is not installed. "
            "Run 'python -c \"from django_angular3.tools import "
            "ensure_speakeasy_openapi; ensure_speakeasy_openapi()\"' "
            "to install it."
        )

    try:
        result = subprocess.run(
            [binary, "spec", "validate", str(path)],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"Speakeasy OpenAPI CLI not found at '{binary}': {exc}"
        ) from exc

    if result.returncode == 0:
        return []

    output = (result.stderr or result.stdout or "").strip()
    if output:
        return [output]
    return [f"openapi spec validate exited with code {result.returncode}."]


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
    """Validate an OpenAPI file using the Speakeasy CLI.

    When the Speakeasy ``openapi`` binary is available, it is invoked as::

        openapi spec validate <path>

    providing full OAS compliance checking.  If the binary is not installed a
    warning is emitted and the lightweight in-process structural check
    (:func:`validate_openapi_document`) is used as a fallback so that the
    package remains usable without Go installed.
    """
    try:
        document = load_document(path)
    except DocumentError as exc:
        return [str(exc)]

    structural_errors = validate_openapi_document(document)
    if structural_errors:
        return structural_errors

    try:
        return _run_speakeasy_validate(path)
    except RuntimeError as exc:
        warnings.warn(
            f"Speakeasy OpenAPI CLI unavailable; falling back to basic validation. "
            f"Install it with 'python -c \"from django_angular3.tools import "
            f"ensure_speakeasy_openapi; ensure_speakeasy_openapi()\"'. "
            f"Details: {exc}",
            stacklevel=2,
        )
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
