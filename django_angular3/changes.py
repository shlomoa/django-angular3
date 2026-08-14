"""Canonical immutable values for the djng Change Model.

Derivation and command translation belong to their respective domain services.
This module owns only the normalized, serializable representation described by
``REQUIREMENTS.md`` §4.2.9.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import cast

type _JsonScalar = str | int | float | bool | None
type _JsonValue = _JsonScalar | tuple[_JsonValue, ...] | Mapping[str, _JsonValue]


def _normalize_json(value: object) -> _JsonValue:
    """Validate and recursively freeze a JSON-compatible Change Model value."""
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("JSON numbers must be finite.")
        return value
    if isinstance(value, Mapping):
        mapping = cast(Mapping[object, object], value)
        if not all(isinstance(key, str) for key in mapping):
            raise TypeError("JSON object keys must be strings.")
        string_mapping = cast(Mapping[str, object], mapping)
        return MappingProxyType(
            {key: _normalize_json(string_mapping[key]) for key in sorted(string_mapping)}
        )
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        sequence = cast(Sequence[object], value)
        return tuple(_normalize_json(item) for item in sequence)
    raise TypeError(f"Value is not JSON-compatible: {type(value).__name__}.")


def _json_value(value: _JsonValue) -> object:
    """Convert a frozen Change Model value into standard JSON values."""
    if isinstance(value, Mapping):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    return value


def _canonical_json(value: object) -> str:
    """Return deterministic JSON for a ChangeSet artifact."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class ChangeDomain(StrEnum):
    """A normalized input domain in the canonical Change Model."""

    STATIC_CONFIG = "static_config"
    PROJECT_CONFIG = "project_config"
    INVOCATION = "invocation"
    OPENAPI = "openapi"
    OPENUI = "openui"


class ChangeOperation(StrEnum):
    """The only operations permitted for an atomic change."""

    CREATE = "create"
    DELETE = "delete"
    UPDATE = "update"
    MOVE = "move"


@dataclass(frozen=True)
class ChangeEvidence:
    """Evidence supporting an atomic change."""

    source: str
    location: str | None = None
    fragment: object | None = None

    def __post_init__(self) -> None:
        if not self.source.strip():
            raise ValueError("Change evidence source must not be empty.")
        if self.location is not None and not self.location.strip():
            raise ValueError("Change evidence location must not be empty when set.")
        if self.fragment is not None:
            object.__setattr__(self, "fragment", _normalize_json(self.fragment))

    def to_dict(self) -> dict[str, object]:
        """Serialize evidence using standard JSON-compatible values."""
        result: dict[str, object] = {"source": self.source}
        if self.location is not None:
            result["location"] = self.location
        if self.fragment is not None:
            result["fragment"] = _json_value(cast(_JsonValue, self.fragment))
        return result


@dataclass(frozen=True)
class Change:
    """One immutable, atomic normalized semantic difference."""

    domain: ChangeDomain
    subject: str
    path: str
    operation: ChangeOperation
    before: object
    after: object
    affected: tuple[str, ...] = ()
    evidence: tuple[ChangeEvidence, ...] = ()

    def __post_init__(self) -> None:
        if not self.subject.strip():
            raise ValueError("Change subject must not be empty.")
        if any(not identity.strip() for identity in self.affected):
            raise ValueError("Affected identities must not be empty.")
        if len(set(self.affected)) != len(self.affected):
            raise ValueError("Affected identities must be unique.")

        frozen_before = _normalize_json(self.before)
        frozen_after = _normalize_json(self.after)
        object.__setattr__(self, "before", frozen_before)
        object.__setattr__(self, "after", frozen_after)

    def to_dict(self) -> dict[str, object]:
        """Serialize the change deterministically."""
        return {
            "domain": self.domain.value,
            "subject": self.subject,
            "path": self.path,
            "operation": self.operation.value,
            "before": _json_value(cast(_JsonValue, self.before)),
            "after": _json_value(cast(_JsonValue, self.after)),
            "affected": list(self.affected),
            "evidence": [item.to_dict() for item in self.evidence],
        }


@dataclass(frozen=True)
class ChangeDomainResult:
    """Atomic changes produced for one Change Model domain."""

    domain: ChangeDomain
    changes: tuple[Change, ...] = ()

    def __post_init__(self) -> None:
        if any(change.domain is not self.domain for change in self.changes):
            raise ValueError("Every change must belong to its domain result domain.")

    @property
    def has_changes(self) -> bool:
        """Whether the domain has atomic changes; no_change is never emitted."""
        return bool(self.changes)

    def to_dict(self) -> dict[str, object]:
        """Serialize the domain result without a redundant category summary."""
        return {"changes": [change.to_dict() for change in self.changes]}


@dataclass(frozen=True)
class ChangeSet:
    """The canonical five-domain set of atomic changes and computed summary."""

    baseline: Mapping[str, object]
    candidate: Mapping[str, object]
    domains: Mapping[ChangeDomain, ChangeDomainResult]
    version: int = 1

    def __post_init__(self) -> None:
        if self.version != 1:
            raise ValueError("Only ChangeSet version 1 is supported.")
        object.__setattr__(self, "baseline", _normalize_json(self.baseline))
        object.__setattr__(self, "candidate", _normalize_json(self.candidate))

        normalized_domains: dict[ChangeDomain, ChangeDomainResult] = {}
        for domain, result in self.domains.items():
            normalized_domain = ChangeDomain(domain)
            if result.domain is not normalized_domain:
                raise ValueError("Domain result key must match its domain.")
            normalized_domains[normalized_domain] = result
        missing_domains = set(ChangeDomain) - set(normalized_domains)
        if missing_domains:
            labels = ", ".join(domain.value for domain in sorted(missing_domains))
            raise ValueError(f"ChangeSet is missing domain result(s): {labels}.")
        object.__setattr__(self, "domains", MappingProxyType(normalized_domains))

    @property
    def has_changes(self) -> bool:
        """Computed summary; an empty atomic list means no change."""
        return any(result.has_changes for result in self.domains.values())

    def to_dict(self) -> dict[str, object]:
        """Serialize the canonical ChangeSet schema."""
        return {
            "version": self.version,
            "baseline": _json_value(cast(_JsonValue, self.baseline)),
            "candidate": _json_value(cast(_JsonValue, self.candidate)),
            "domains": {
                domain.value: self.domains[domain].to_dict() for domain in ChangeDomain
            },
            "summary": {"hasChanges": self.has_changes},
        }

    def to_json(self) -> str:
        """Return deterministic JSON suitable for a durable ChangeSet artifact."""
        return _canonical_json(self.to_dict())
