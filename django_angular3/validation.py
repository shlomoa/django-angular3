from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import ProjectConfig
from .documents import DocumentError, load_document


class ValidationError(ValueError):
    """Raised when validation cannot continue."""


def validate_openapi_document(document: Any) -> list[str]:
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
            errors.append(f"OpenAPI path '{path_name}' must be a string starting with '/'.")
            continue
        if not isinstance(path_item, dict):
            errors.append(f"OpenAPI path '{path_name}' must map to an object.")
            continue

        operations = [name for name in path_item if name in allowed_methods]
        if not operations:
            errors.append(f"OpenAPI path '{path_name}' must define at least one HTTP operation.")
            continue

        for operation_name in operations:
            operation = path_item[operation_name]
            if not isinstance(operation, dict):
                errors.append(
                    f"Operation '{operation_name}' on path '{path_name}' must be an object."
                )

    return errors


def validate_ui_document(document: Any) -> list[str]:
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
                errors.append(f"pages[{index}].route must be a string starting with '/'.")
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
                    errors.append(f"forms[{index}].submit must be an object when provided.")
                else:
                    action = submit.get("action")
                    if not isinstance(action, str) or not action.strip():
                        errors.append(
                            f"forms[{index}].submit.action must be a non-empty string."
                        )

    return errors


def validate_openapi_file(path: str | Path) -> list[str]:
    try:
        document = load_document(path)
    except DocumentError as exc:
        return [str(exc)]
    return validate_openapi_document(document)


def validate_ui_file(path: str | Path) -> list[str]:
    try:
        document = load_document(path)
    except DocumentError as exc:
        return [str(exc)]
    return validate_ui_document(document)


def validate_project_config(config: ProjectConfig) -> list[str]:
    errors: list[str] = []

    if not config.openapi_source.exists():
        errors.append(f"OpenAPI source does not exist: {config.openapi_source}")
    else:
        errors.extend(validate_openapi_file(config.openapi_source))

    if not config.ui_source.exists():
        errors.append(f"UI source does not exist: {config.ui_source}")
    else:
        errors.extend(validate_ui_file(config.ui_source))

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
            "ng-openapi-gen config does not exist: "
            f"{config.ng_openapi_gen_config}"
        )

    return errors
