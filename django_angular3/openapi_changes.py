"""Translate a supported oasdiff detail document into canonical Changes."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

from .changes import Change, ChangeDomain, ChangeEvidence, ChangeOperation
from .documents import DocumentError, load_document
from .external_comparisons import run_oasdiff_diff
from .validation import validate_openapi_document


class OpenApiComparisonError(ValueError):
    """Raised when an OpenAPI comparison input or oasdiff detail is unsupported."""


def compare_openapi_files(
    reference: Path | None, candidate: Path
) -> tuple[Change, ...]:
    """Validate OpenAPI inputs and derive canonical changes through oasdiff."""
    candidate_document = _load_openapi_document(candidate)
    if reference is None:
        return _create_document_changes(candidate_document, str(candidate))

    reference_document = _load_openapi_document(reference)
    return translate_oasdiff_detail(
        run_oasdiff_diff(reference, candidate),
        reference_document,
        candidate_document,
        source=str(candidate),
    )


def translate_oasdiff_detail(
    detail: Mapping[str, object],
    reference: Mapping[str, object],
    candidate: Mapping[str, object],
    *,
    source: str,
) -> tuple[Change, ...]:
    """Translate supported ``oasdiff diff --format json`` detail into Changes.

    The evaluator supports paths, operations within modified paths, and component
    schemas. Unsupported detail is rejected rather than silently treated as no
    change. Native oasdiff fragments remain the evidence for every Change.
    """
    if not isinstance(detail, Mapping):
        raise OpenApiComparisonError("oasdiff detail must be an object.")
    if not detail:
        return ()
    _require_supported_keys(detail, {"paths", "components"}, "oasdiff detail")

    changes: list[Change] = []
    if "paths" in detail:
        changes.extend(_path_changes(detail["paths"], reference, candidate, source))
    if "components" in detail:
        changes.extend(
            _component_schema_changes(
                detail["components"], reference, candidate, source
            )
        )
    return tuple(changes)


def _load_openapi_document(path: Path) -> Mapping[str, object]:
    try:
        document = load_document(path)
    except DocumentError as exc:
        raise OpenApiComparisonError(str(exc)) from exc
    if not isinstance(document, Mapping):
        raise OpenApiComparisonError("OpenAPI document must be an object.")
    errors = validate_openapi_document(document)
    if errors:
        raise OpenApiComparisonError("Invalid OpenAPI document: " + "; ".join(errors))
    return cast(Mapping[str, object], document)


def _path_changes(
    detail: object,
    reference: Mapping[str, object],
    candidate: Mapping[str, object],
    source: str,
) -> list[Change]:
    diff = _mapping(detail, "oasdiff paths")
    _require_supported_keys(diff, {"added", "deleted", "modified"}, "oasdiff paths")
    changes: list[Change] = []
    for operation, category, document in (
        (ChangeOperation.CREATE, "added", candidate),
        (ChangeOperation.DELETE, "deleted", reference),
    ):
        for path in _string_list(diff.get(category, []), f"oasdiff paths.{category}"):
            changes.append(
                _change(
                    subject=f"path:{path}",
                    path=_pointer("paths", path),
                    operation=operation,
                    before=(
                        None
                        if operation is ChangeOperation.CREATE
                        else _value(document, "paths", path)
                    ),
                    after=(
                        _value(document, "paths", path)
                        if operation is ChangeOperation.CREATE
                        else None
                    ),
                    source=source,
                    fragment={"category": category, "path": path},
                    affected=(f"path:{path}",),
                )
            )
    modified = _mapping(diff.get("modified", {}), "oasdiff paths.modified")
    for path in sorted(modified):
        path_detail = _mapping(modified[path], f"oasdiff path '{path}'")
        _require_supported_keys(path_detail, {"operations"}, f"oasdiff path '{path}'")
        if "operations" not in path_detail:
            continue
        changes.extend(
            _operation_changes(
                path, path_detail["operations"], reference, candidate, source
            )
        )
    return changes


def _operation_changes(
    path: str,
    detail: object,
    reference: Mapping[str, object],
    candidate: Mapping[str, object],
    source: str,
) -> list[Change]:
    diff = _mapping(detail, f"oasdiff operations for '{path}'")
    _require_supported_keys(
        diff, {"added", "deleted", "modified"}, f"oasdiff operations for '{path}'"
    )
    changes: list[Change] = []
    for operation, category, document in (
        (ChangeOperation.CREATE, "added", candidate),
        (ChangeOperation.DELETE, "deleted", reference),
    ):
        for method in _string_list(
            diff.get(category, []), f"oasdiff operations.{category}"
        ):
            changes.append(
                _change(
                    subject=f"operation:{method.upper()} {path}",
                    path=_pointer("paths", path, method.lower()),
                    operation=operation,
                    before=(
                        None
                        if operation is ChangeOperation.CREATE
                        else _value(document, "paths", path, method.lower())
                    ),
                    after=(
                        _value(document, "paths", path, method.lower())
                        if operation is ChangeOperation.CREATE
                        else None
                    ),
                    source=source,
                    fragment={"category": category, "method": method, "path": path},
                    affected=(f"path:{path}",),
                )
            )
    modified = _mapping(diff.get("modified", {}), "oasdiff operations.modified")
    for method in sorted(modified):
        fragment = _mapping(modified[method], f"oasdiff operation '{method}'")
        changes.append(
            _change(
                subject=f"operation:{method.upper()} {path}",
                path=_pointer("paths", path, method.lower()),
                operation=ChangeOperation.UPDATE,
                before=_value(reference, "paths", path, method.lower()),
                after=_value(candidate, "paths", path, method.lower()),
                source=source,
                fragment=fragment,
                affected=(f"path:{path}",),
            )
        )
    return changes


def _component_schema_changes(
    detail: object,
    reference: Mapping[str, object],
    candidate: Mapping[str, object],
    source: str,
) -> list[Change]:
    components = _mapping(detail, "oasdiff components")
    _require_supported_keys(components, {"schemas"}, "oasdiff components")
    if "schemas" not in components:
        return []
    diff = _mapping(components["schemas"], "oasdiff component schemas")
    _require_supported_keys(
        diff, {"added", "deleted", "modified"}, "oasdiff component schemas"
    )
    changes: list[Change] = []
    for operation, category, document in (
        (ChangeOperation.CREATE, "added", candidate),
        (ChangeOperation.DELETE, "deleted", reference),
    ):
        for name in _string_list(diff.get(category, []), f"oasdiff schemas.{category}"):
            changes.append(
                _change(
                    subject=f"schema:{name}",
                    path=_pointer("components", "schemas", name),
                    operation=operation,
                    before=(
                        None
                        if operation is ChangeOperation.CREATE
                        else _value(document, "components", "schemas", name)
                    ),
                    after=(
                        _value(document, "components", "schemas", name)
                        if operation is ChangeOperation.CREATE
                        else None
                    ),
                    source=source,
                    fragment={"category": category, "schema": name},
                    affected=(f"schema:{name}",),
                )
            )
    modified = _mapping(diff.get("modified", {}), "oasdiff schemas.modified")
    for name in sorted(modified):
        fragment = _mapping(modified[name], f"oasdiff schema '{name}'")
        changes.append(
            _change(
                subject=f"schema:{name}",
                path=_pointer("components", "schemas", name),
                operation=ChangeOperation.UPDATE,
                before=_value(reference, "components", "schemas", name),
                after=_value(candidate, "components", "schemas", name),
                source=source,
                fragment=fragment,
                affected=(f"schema:{name}",),
            )
        )
    return changes


def _create_document_changes(
    document: Mapping[str, object], source: str
) -> tuple[Change, ...]:
    paths = _mapping(document.get("paths"), "OpenAPI paths")
    changes: list[Change] = []
    for path in sorted(paths):
        changes.append(
            _change(
                subject=f"path:{path}",
                path=_pointer("paths", path),
                operation=ChangeOperation.CREATE,
                before=None,
                after=paths[path],
                source=source,
                fragment={"category": "initial", "path": path},
                affected=(f"path:{path}",),
            )
        )
    components = document.get("components", {})
    if components:
        schemas = _mapping(
            _mapping(components, "OpenAPI components").get("schemas", {}),
            "OpenAPI component schemas",
        )
        for name in sorted(schemas):
            changes.append(
                _change(
                    subject=f"schema:{name}",
                    path=_pointer("components", "schemas", name),
                    operation=ChangeOperation.CREATE,
                    before=None,
                    after=schemas[name],
                    source=source,
                    fragment={"category": "initial", "schema": name},
                    affected=(f"schema:{name}",),
                )
            )
    return tuple(changes)


def _change(
    *,
    subject: str,
    path: str,
    operation: ChangeOperation,
    before: object,
    after: object,
    source: str,
    fragment: Mapping[str, object],
    affected: tuple[str, ...],
) -> Change:
    return Change(
        domain=ChangeDomain.OPENAPI,
        subject=subject,
        path=path,
        operation=operation,
        before=before,
        after=after,
        affected=affected,
        evidence=(ChangeEvidence(source, location=path, fragment=fragment),),
    )


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or not all(isinstance(key, str) for key in value):
        raise OpenApiComparisonError(f"{label} must be an object.")
    return cast(Mapping[str, object], value)


def _string_list(value: object, label: str) -> tuple[str, ...]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, str)
        or not all(isinstance(item, str) for item in value)
    ):
        raise OpenApiComparisonError(f"{label} must be a list of strings.")
    return tuple(sorted(cast(Sequence[str], value)))


def _require_supported_keys(
    document: Mapping[str, object], supported: set[str], label: str
) -> None:
    unsupported = set(document) - supported
    if unsupported:
        raise OpenApiComparisonError(
            f"{label} contains unsupported key(s): {', '.join(sorted(unsupported))}."
        )


def _value(document: Mapping[str, object], *tokens: str) -> object:
    value: object = document
    for token in tokens:
        if not isinstance(value, Mapping) or token not in value:
            raise OpenApiComparisonError(
                f"oasdiff detail references absent OpenAPI value: {_pointer(*tokens)}."
            )
        value = value[token]
    return value


def _pointer(*tokens: str) -> str:
    return "/" + "/".join(
        token.replace("~", "~0").replace("/", "~1") for token in tokens
    )
