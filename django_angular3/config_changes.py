"""Derive canonical Change values from djng-owned configuration domains."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final, cast

from .changes import Change, ChangeDomain, ChangeEvidence, ChangeOperation
from .config import ProjectConfig
from .settings import validate_tool_configuration

_MISSING: Final = object()
_COMMAND_ALLOWLIST_PATH: Final = ("tool", "commandAllowlist")


@dataclass(frozen=True)
class _ConfigComparison:
    domain: ChangeDomain
    source: str

    def change(
        self,
        path_tokens: tuple[str, ...],
        operation: ChangeOperation,
        before: object,
        after: object,
    ) -> Change:
        path = _json_pointer(path_tokens)
        return Change(
            domain=self.domain,
            subject=".".join(path_tokens),
            path=path,
            operation=operation,
            before=before,
            after=after,
            evidence=(ChangeEvidence(self.source, location=path),),
        )


def compare_static_config(
    baseline: Mapping[str, object] | None,
    candidate: Mapping[str, object],
    *,
    source: str = "django-angular3.json",
) -> tuple[Change, ...]:
    """Compare accepted django-angular3.json values into static-config Changes."""
    _validate_static_config(candidate)
    if baseline is not None:
        _validate_static_config(baseline)

    comparison = _ConfigComparison(ChangeDomain.STATIC_CONFIG, source)
    return tuple(
        _compare_mapping(
            comparison,
            (),
            {} if baseline is None else baseline,
            candidate,
        )
    )


def compare_project_config(
    baseline: ProjectConfig | None,
    candidate: ProjectConfig,
) -> tuple[Change, ...]:
    """Compare project identity and artifact selectors into project-config Changes."""
    comparison = _ConfigComparison(
        ChangeDomain.PROJECT_CONFIG, str(candidate.config_path)
    )
    fields = (
        (("project", "name"), "project_name"),
        (("artifacts", "openapiSchema"), "openapi_schema"),
        (("artifacts", "openuiSpecification"), "openui_specification"),
        (("artifacts", "angularWorkspace"), "angular_workspace"),
    )

    changes: list[Change] = []
    for path_tokens, attribute in fields:
        after = _project_value(getattr(candidate, attribute))
        if baseline is None:
            before = None
            changes.append(
                comparison.change(path_tokens, ChangeOperation.CREATE, None, after)
            )
            continue

        before = _project_value(getattr(baseline, attribute))
        if before != after:
            changes.append(
                comparison.change(path_tokens, ChangeOperation.UPDATE, before, after)
            )
    return tuple(changes)


def _project_value(value: object) -> str:
    return value.as_posix() if isinstance(value, Path) else str(value)


def _validate_static_config(document: Mapping[str, object]) -> None:
    errors = validate_tool_configuration(document)
    if errors:
        raise ValueError("Invalid django-angular3.json: " + "; ".join(errors))


def _compare_mapping(
    comparison: _ConfigComparison,
    parent: tuple[str, ...],
    baseline: Mapping[str, object],
    candidate: Mapping[str, object],
) -> list[Change]:
    changes: list[Change] = []
    for key in sorted(set(baseline) | set(candidate)):
        path_tokens = (*parent, key)
        before = baseline.get(key, _MISSING)
        after = candidate.get(key, _MISSING)
        if before is _MISSING:
            changes.extend(_create_changes(comparison, path_tokens, after))
        elif after is _MISSING:
            changes.extend(_delete_changes(comparison, path_tokens, before))
        elif isinstance(before, Mapping) and isinstance(after, Mapping):
            changes.extend(
                _compare_mapping(
                    comparison,
                    path_tokens,
                    cast(Mapping[str, object], before),
                    cast(Mapping[str, object], after),
                )
            )
        elif path_tokens == _COMMAND_ALLOWLIST_PATH:
            changes.extend(
                _compare_command_allowlist(
                    comparison, path_tokens, cast(object, before), cast(object, after)
                )
            )
        elif before != after:
            changes.append(
                comparison.change(path_tokens, ChangeOperation.UPDATE, before, after)
            )
    return changes


def _create_changes(
    comparison: _ConfigComparison, path_tokens: tuple[str, ...], value: object
) -> list[Change]:
    if isinstance(value, Mapping):
        mapping = cast(Mapping[str, object], value)
        return [
            change
            for key in sorted(mapping)
            for change in _create_changes(comparison, (*path_tokens, key), mapping[key])
        ]
    if path_tokens == _COMMAND_ALLOWLIST_PATH:
        return [
            comparison.change(
                (*path_tokens, command), ChangeOperation.CREATE, None, command
            )
            for command in _normalized_allowlist(value)
        ]
    return [comparison.change(path_tokens, ChangeOperation.CREATE, None, value)]


def _delete_changes(
    comparison: _ConfigComparison, path_tokens: tuple[str, ...], value: object
) -> list[Change]:
    if isinstance(value, Mapping):
        mapping = cast(Mapping[str, object], value)
        return [
            change
            for key in sorted(mapping)
            for change in _delete_changes(comparison, (*path_tokens, key), mapping[key])
        ]
    if path_tokens == _COMMAND_ALLOWLIST_PATH:
        return [
            comparison.change(
                (*path_tokens, command), ChangeOperation.DELETE, command, None
            )
            for command in _normalized_allowlist(value)
        ]
    return [comparison.change(path_tokens, ChangeOperation.DELETE, value, None)]


def _compare_command_allowlist(
    comparison: _ConfigComparison,
    path_tokens: tuple[str, ...],
    baseline: object,
    candidate: object,
) -> list[Change]:
    before = set(_normalized_allowlist(baseline))
    after = set(_normalized_allowlist(candidate))
    return [
        comparison.change(
            (*path_tokens, command), ChangeOperation.DELETE, command, None
        )
        for command in sorted(before - after)
    ] + [
        comparison.change(
            (*path_tokens, command), ChangeOperation.CREATE, None, command
        )
        for command in sorted(after - before)
    ]


def _normalized_allowlist(value: object) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, str):
        raise ValueError("tool.commandAllowlist must be a sequence of strings.")
    commands = cast(Sequence[object], value)
    return tuple(
        sorted(
            {
                command.strip().lower()
                for command in commands
                if isinstance(command, str)
            }
        )
    )


def _json_pointer(tokens: tuple[str, ...]) -> str:
    return "/" + "/".join(
        token.replace("~", "~0").replace("/", "~1") for token in tokens
    )
