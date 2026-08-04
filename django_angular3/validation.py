from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

from .config import ProjectConfig
from .documents import DocumentError, load_document


class ValidationError(ValueError):
    """Raised when validation cannot continue."""


# ---------------------------------------------------------------------------
# Speakeasy OpenAPI CLI helpers
# ---------------------------------------------------------------------------

_SPEAKEASY_OPENAPI_BIN = "openapi"


def _find_speakeasy_openapi() -> str | None:
    """Return the path to the Speakeasy ``openapi`` binary, or None."""
    # Prefer the binary installed via ensure_speakeasy_openapi() in GOPATH/bin
    import os
    import platform

    try:
        result = subprocess.run(
            ["go", "env", "GOPATH"],
            capture_output=True,
            text=True,
            check=True,
        )
        gopath = result.stdout.strip()
    except Exception:
        gopath = ""

    if gopath:
        exe = "openapi.exe" if platform.system().lower() == "windows" else "openapi"
        candidate = Path(gopath) / "bin" / exe
        if candidate.exists() and os.access(candidate, os.X_OK):
            return str(candidate)

    return shutil.which(_SPEAKEASY_OPENAPI_BIN)


def _run_speakeasy_validate(path: str | Path) -> list[str]:
    """Run ``openapi spec validate`` against *path*.

    Returns a list of error strings (empty if valid).
    Raises ``RuntimeError`` if the binary cannot be found.
    """
    binary = _find_speakeasy_openapi()
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

    # Collect error output
    output = (result.stderr or result.stdout or "").strip()
    if output:
        return [output]
    return [f"openapi spec validate exited with code {result.returncode}."]


def validate_openapi_document(document: Any) -> list[str]:
    """Lightweight structural pre-check for an in-memory OpenAPI document.

    This is intentionally minimal — full OAS compliance is delegated to the
    Speakeasy ``openapi spec validate`` CLI (see :func:`validate_openapi_file`).
    """
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
    errors: list[str] = []
    if not isinstance(document, dict):
        return ["UI definition document must be a mapping."]

    pages = document.get("pages", [])
    forms = document.get("forms", [])

    if not isinstance(pages, list):
        errors.append("'pages' must be a list when provided.")
    else:
        for index, page in enumerate(pages):
            if not isinstance(page, dict):
                errors.append(f"pages[{index}] must be an object.")
                continue
            route = page.get("route")
            kind = page.get("kind")
            if not isinstance(route, str) or not route.startswith("/"):
                errors.append(
                    f"pages[{index}].route must be a string starting with '/'."
                )
            if not isinstance(kind, str) or not kind.strip():
                errors.append(f"pages[{index}].kind must be a non-empty string.")

    if not isinstance(forms, list):
        errors.append("'forms' must be a list when provided.")
    else:
        for index, form in enumerate(forms):
            if not isinstance(form, dict):
                errors.append(f"forms[{index}] must be an object.")
                continue
            form_id = form.get("id")
            mode = form.get("mode")
            submit = form.get("submit")
            if not isinstance(form_id, str) or not form_id.strip():
                errors.append(f"forms[{index}].id must be a non-empty string.")
            if not isinstance(mode, str) or not mode.strip():
                errors.append(f"forms[{index}].mode must be a non-empty string.")
            if submit is not None:
                if not isinstance(submit, dict):
                    errors.append(
                        f"forms[{index}].submit must be an object when provided."
                    )
                else:
                    action = submit.get("action")
                    if not isinstance(action, str) or not action.strip():
                        errors.append(
                            f"forms[{index}].submit.action must be a non-empty string."
                        )

    return errors


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

    # Run quick structural checks first — fast feedback for obviously broken docs
    structural_errors = validate_openapi_document(document)
    if structural_errors:
        return structural_errors

    # Delegate to the Speakeasy CLI for full OAS compliance validation
    try:
        return _run_speakeasy_validate(path)
    except RuntimeError as exc:
        import warnings

        warnings.warn(
            f"Speakeasy OpenAPI CLI unavailable; falling back to basic validation. "
            f"Install it with 'python -c \"from django_angular3.tools import "
            f"ensure_speakeasy_openapi; ensure_speakeasy_openapi()\"'. "
            f"Details: {exc}",
            stacklevel=2,
        )
        return []


def validate_openui_file(path: str | Path) -> list[str]:
    try:
        document = load_document(path)
    except DocumentError as exc:
        return [str(exc)]
    return validate_openui_document(document)


def validate_project_config(config: ProjectConfig) -> list[str]:
    errors: list[str] = []

    if not config.openapi_source.exists():
        errors.append(f"OpenAPI source does not exist: {config.openapi_source}")
    else:
        errors.extend(validate_openapi_file(config.openapi_source))

    if not config.openui_source.exists():
        errors.append(f"UI source does not exist: {config.openui_source}")
    else:
        errors.extend(validate_openui_file(config.openui_source))

    if config.angular_output.exists() and not config.angular_output.is_dir():
        errors.append(
            "Angular output path must be a directory when it exists: "
            f"{config.angular_output}"
        )

    if config.openapi_generator_config and not config.openapi_generator_config.exists():
        errors.append(
            "OpenAPI Generator config does not exist: "
            f"{config.openapi_generator_config}"
        )

    if config.ng_openapi_gen_config and not config.ng_openapi_gen_config.exists():
        errors.append(
            f"ng-openapi-gen config does not exist: {config.ng_openapi_gen_config}"
        )

    return errors
