"""Immutable, serializable provider-neutral automation contracts.

Standard library only. The models here are the shared vocabulary of Tool, Hook
and adapter results (AIR-1, AIR-2). Serialization is deterministic (AIR-NFR-1):
sorted keys, fixed separators, UTF-8, and no timestamps or identifiers that the
caller did not inject.

The evidence policy of ``AI_AUTOMATION_SPECIFICATIONS.md`` §3.1 is defined once,
in :func:`apply_evidence_policy`; the recorder calls it at the write boundary.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum, StrEnum
from types import MappingProxyType
from typing import Any, Protocol

REDACTED = "[REDACTED]"


class FailureCategory(StrEnum):
    """Failure categories distinguished by callers (``TOOL_CONTRACTS.md``,
    ``PROVIDER_ADAPTER_CONTRACTS.md``, ``HOOK_CONTRACTS.md``)."""

    INVALID_INPUT = "invalid_input"
    MISSING_DEPENDENCY = "missing_dependency"
    EXTERNAL_TOOL_FAILED = "external_tool_failed"
    OUTPUT_INVALID = "output_invalid"
    HOOK_FAILED = "hook_failed"
    UNMET_ACCEPTANCE = "unmet_acceptance"
    TOOL_DENIED = "tool_denied"
    TIMEOUT = "timeout"
    CONTEXT_EXHAUSTED = "context_exhausted"
    EVIDENCE_REJECTED = "evidence_rejected"
    EVIDENCE_WRITE_FAILED = "evidence_write_failed"
    UNEXPECTED = "unexpected"


class HookFamily(StrEnum):
    """Provider-neutral lifecycle families (``HOOK_CONTRACTS.md``)."""

    PRE_TOOL = "pre-tool"
    POST_TOOL = "post-tool"
    SESSION_STOP = "session-stop"


class Consequence(StrEnum):
    """Consequence of a failing Hook, fixed by its lifecycle family (AIR-5)."""

    BLOCK = "block"
    HALT = "halt"
    WARN = "warn"


#: A failing pre-tool Hook blocks, post-tool halts, session-stop only warns.
FAMILY_CONSEQUENCE = MappingProxyType(
    {
        HookFamily.PRE_TOOL: Consequence.BLOCK,
        HookFamily.POST_TOOL: Consequence.HALT,
        HookFamily.SESSION_STOP: Consequence.WARN,
    }
)


class AdapterStatus(StrEnum):
    """Normalized adapter outcomes (``PROVIDER_ADAPTER_CONTRACTS.md``)."""

    ACCEPTED = "accepted"
    UNMET_ACCEPTANCE = "unmet_acceptance"
    TIMEOUT = "timeout"
    CONTEXT_EXHAUSTED = "context_exhausted"
    TOOL_DENIED = "tool_denied"


class ContractError(ValueError):
    """A contract failed validation; carries the structured failure."""

    def __init__(
        self,
        category: FailureCategory,
        message: str,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.category = category
        self.message = message
        self.details = dict(details or {})

    def to_failure(self) -> AutomationFailure:
        return AutomationFailure(self.category, self.message, self.details)


# -- freezing and serialization ------------------------------------------------


def _freeze(value: Any, path: str = "value") -> Any:
    """Deep-freeze a JSON-compatible value; reject everything else."""
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise ContractError(
                FailureCategory.INVALID_INPUT, f"{path} is not a finite number"
            )
        return value
    if isinstance(value, Mapping):
        items = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise ContractError(
                    FailureCategory.INVALID_INPUT, f"{path} has a non-string key"
                )
            items[key] = _freeze(item, f"{path}.{key}")
        return MappingProxyType(dict(sorted(items.items())))
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item, f"{path}[{i}]") for i, item in enumerate(value))
    raise ContractError(
        FailureCategory.INVALID_INPUT,
        f"{path} is not JSON-serializable ({type(value).__name__})",
    )


def to_jsonable(value: Any) -> Any:
    """Return plain dict/list structures for a frozen value or contract."""
    if isinstance(value, _Contract):
        return value.to_dict()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {key: to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    return value


def dumps(value: Any) -> str:
    """Deterministic JSON: sorted keys, fixed separators, no ASCII escaping."""
    return json.dumps(
        to_jsonable(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _require(
    data: Mapping[str, Any], key: str, kind: type | tuple[type, ...], what: str
) -> Any:
    if key not in data:
        raise ContractError(
            FailureCategory.INVALID_INPUT, f"{what}: missing field '{key}'"
        )
    value = data[key]
    if isinstance(value, bool) and bool not in (
        kind if isinstance(kind, tuple) else (kind,)
    ):
        raise ContractError(
            FailureCategory.INVALID_INPUT, f"{what}: field '{key}' has the wrong type"
        )
    if not isinstance(value, kind):
        raise ContractError(
            FailureCategory.INVALID_INPUT, f"{what}: field '{key}' has the wrong type"
        )
    return value


def _enum(enum_type: type[Enum], value: Any, what: str) -> Any:
    try:
        return enum_type(value)
    except ValueError:
        raise ContractError(
            FailureCategory.INVALID_INPUT,
            f"{what}: unknown {enum_type.__name__} '{value}'",
        ) from None


def _reject_unknown(data: Mapping[str, Any], allowed: set[str], what: str) -> None:
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise ContractError(
            FailureCategory.INVALID_INPUT, f"{what}: unknown fields {unknown}"
        )


class _Contract:
    """Base for contracts: ``to_dict`` / ``to_json`` are deterministic."""

    def to_dict(self) -> dict[str, Any]:  # pragma: no cover - overridden
        raise NotImplementedError

    def to_json(self) -> str:
        return dumps(self)


# -- models --------------------------------------------------------------------


@dataclass(frozen=True)
class AutomationFailure(_Contract):
    """Structured failure ``{ category, message, details }``."""

    category: FailureCategory
    message: str
    details: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.category, FailureCategory):
            raise ContractError(
                FailureCategory.INVALID_INPUT, "failure: category is not a category"
            )
        if not isinstance(self.message, str) or not self.message:
            raise ContractError(
                FailureCategory.INVALID_INPUT, "failure: message must be non-empty"
            )
        object.__setattr__(self, "details", _freeze(self.details, "failure.details"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category.value,
            "details": to_jsonable(self.details),
            "message": self.message,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> AutomationFailure:
        what = "failure"
        _reject_unknown(data, {"category", "message", "details"}, what)
        return cls(
            _enum(FailureCategory, _require(data, "category", str, what), what),
            _require(data, "message", str, what),
            _require(data, "details", Mapping, what),
        )


@dataclass(frozen=True)
class ToolResult(_Contract):
    """Normalized Tool outcome: structured output or a structured failure."""

    tool: str
    output: Mapping[str, Any]
    failure: AutomationFailure | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.tool, str) or not self.tool:
            raise ContractError(
                FailureCategory.INVALID_INPUT, "tool result: tool must be non-empty"
            )
        object.__setattr__(self, "output", _freeze(self.output, "tool result.output"))
        if self.failure is not None and not isinstance(self.failure, AutomationFailure):
            raise ContractError(
                FailureCategory.INVALID_INPUT, "tool result: failure has the wrong type"
            )
        if self.failure is not None and self.output:
            raise ContractError(
                FailureCategory.INVALID_INPUT,
                "tool result: a failed result carries no output",
            )

    @property
    def ok(self) -> bool:
        return self.failure is None

    def to_dict(self) -> dict[str, Any]:
        return {
            "failure": None if self.failure is None else self.failure.to_dict(),
            "ok": self.ok,
            "output": to_jsonable(self.output),
            "tool": self.tool,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ToolResult:
        what = "tool result"
        _reject_unknown(data, {"tool", "output", "failure", "ok"}, what)
        failure = data.get("failure")
        return cls(
            _require(data, "tool", str, what),
            _require(data, "output", Mapping, what),
            None
            if failure is None
            else AutomationFailure.from_dict(_as_mapping(failure, what)),
        )


@dataclass(frozen=True)
class HookOutcome(_Contract):
    """Normalized Hook outcome. The consequence follows the lifecycle family."""

    hook: str
    family: HookFamily
    failure: AutomationFailure | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.hook, str) or not self.hook:
            raise ContractError(
                FailureCategory.INVALID_INPUT, "hook outcome: hook must be non-empty"
            )
        if not isinstance(self.family, HookFamily):
            raise ContractError(
                FailureCategory.INVALID_INPUT, "hook outcome: family has the wrong type"
            )

    @property
    def ok(self) -> bool:
        return self.failure is None

    @property
    def consequence(self) -> Consequence | None:
        """The consequence to apply, or ``None`` when the Hook passed."""
        return None if self.ok else FAMILY_CONSEQUENCE[self.family]

    def to_dict(self) -> dict[str, Any]:
        return {
            "consequence": None if self.consequence is None else self.consequence.value,
            "failure": None if self.failure is None else self.failure.to_dict(),
            "family": self.family.value,
            "hook": self.hook,
            "ok": self.ok,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> HookOutcome:
        what = "hook outcome"
        _reject_unknown(data, {"hook", "family", "failure", "ok", "consequence"}, what)
        failure = data.get("failure")
        return cls(
            _require(data, "hook", str, what),
            _enum(HookFamily, _require(data, "family", str, what), what),
            None
            if failure is None
            else AutomationFailure.from_dict(_as_mapping(failure, what)),
        )


@dataclass(frozen=True)
class AdapterResult(_Contract):
    """Normalized result a provider adapter returns to ``build_app``.

    An adapter never writes evidence or changes the run outcome itself; it only
    returns this value (AIR-3, AIR-7).
    """

    status: AdapterStatus
    evidence: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.status, AdapterStatus):
            raise ContractError(
                FailureCategory.INVALID_INPUT, "adapter result: status is invalid"
            )
        object.__setattr__(
            self, "evidence", _freeze(self.evidence, "adapter result.evidence")
        )

    @property
    def accepted(self) -> bool:
        return self.status is AdapterStatus.ACCEPTED

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence": to_jsonable(self.evidence),
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> AdapterResult:
        what = "adapter result"
        _reject_unknown(data, {"status", "evidence"}, what)
        return cls(
            _enum(AdapterStatus, _require(data, "status", str, what), what),
            _require(data, "evidence", Mapping, what),
        )


class ProviderAdapter(Protocol):
    """Non-mutating adapter protocol: takes a frozen request, returns a result.

    The request is a frozen mapping, so an adapter cannot mutate its input; it
    must not write to the authoritative evidence stream.
    """

    def run(self, request: Mapping[str, Any]) -> AdapterResult: ...


def freeze_request(request: Mapping[str, Any]) -> Mapping[str, Any]:
    """Return the deeply frozen, key-sorted copy handed to an adapter."""
    return _freeze(request, "request")


def _as_mapping(value: Any, what: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ContractError(
            FailureCategory.INVALID_INPUT, f"{what}: expected a mapping"
        )
    return value


# -- evidence policy (AI_AUTOMATION_SPECIFICATIONS.md §3.1) --------------------

_PROVIDER_PAYLOAD_KEYS = frozenset({"provider_payload", "raw_response", "native"})
_HEADER_MAPPING_KEYS = frozenset({"headers", "request_headers"})
_SENSITIVE_SUFFIXES = (
    "authorization",
    "cookie",
    "set-cookie",
    "password",
    "secret",
    "token",
    "api-key",
    "credential",
    "credentials",
)
_CREDENTIAL_PATTERN = re.compile(r"\b(Bearer|Basic)\s+[A-Za-z0-9._~+/=-]+")


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("_", "-")
    return normalized in _HEADER_MAPPING_KEYS or normalized.endswith(
        _SENSITIVE_SUFFIXES
    )


def apply_evidence_policy(record: Any, path: str = "record") -> Any:
    """Return ``record`` with sensitive values redacted.

    Raises :class:`ContractError` (``evidence_rejected``) for a record that
    carries a provider-native payload. Deterministic: depends only on field
    names and value patterns. The input is not mutated.
    """
    if isinstance(record, Mapping):
        result: dict[str, Any] = {}
        for key, item in record.items():
            if not isinstance(key, str):
                raise ContractError(
                    FailureCategory.INVALID_INPUT, f"{path} has a non-string key"
                )
            if key.lower() in _PROVIDER_PAYLOAD_KEYS:
                raise ContractError(
                    FailureCategory.EVIDENCE_REJECTED,
                    "evidence carries a provider-native payload",
                    {"field": f"{path}.{key}"},
                )
            if _is_sensitive_key(key):
                result[key] = REDACTED
            else:
                result[key] = apply_evidence_policy(item, f"{path}.{key}")
        return result
    if isinstance(record, (list, tuple)):
        return [
            apply_evidence_policy(item, f"{path}[{i}]") for i, item in enumerate(record)
        ]
    if isinstance(record, str):
        return _CREDENTIAL_PATTERN.sub(REDACTED, record)
    return record
