"""Durable provider-independent evidence recording (AIR-3, AIR-NFR-1, AIR-NFR-2).

``EvidenceRecorder`` is append-only and dependency-injected. It writes stable UTF-8
JSON Lines below the selected build output: one run record, then ordered Tool, Hook
and acceptance events. Identifiers and timestamps come from the execution boundary
(the run identifier and the clock are injected), never from hidden global state, so
identical injected values give byte-identical files. Every completed event is flushed
so a halted run stays inspectable. The evidence policy of the contracts module
(redaction, rejection of provider-native payloads) is applied at the write boundary.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Protocol

from .contracts import (
    ContractError,
    FailureCategory,
    apply_evidence_policy,
    dumps,
)

EVIDENCE_FILE_NAME: Final = "automation-evidence.jsonl"

KIND_RUN: Final = "run"
KIND_TOOL: Final = "tool"
KIND_HOOK: Final = "hook"
KIND_ACCEPTANCE: Final = "acceptance"
EVENT_KINDS: Final = frozenset({KIND_RUN, KIND_TOOL, KIND_HOOK, KIND_ACCEPTANCE})

#: Fields the recorder owns; a caller payload cannot set them.
_RESERVED: Final = frozenset({"kind", "run_id", "seq", "timestamp"})

Clock = Callable[[], str]


class EvidenceRecorder(Protocol):
    """What the execution boundary needs from a recorder."""

    def record(self, kind: str, payload: Mapping[str, Any]) -> None:
        """Append one event; raises ``ContractError`` on a rejected or failed write."""
        ...


class NoOpEvidenceRecorder:
    """Records nothing and writes no file (dry runs and callers without evidence)."""

    def record(self, kind: str, payload: Mapping[str, Any]) -> None:
        return None


@dataclass(frozen=True)
class ReadEvents:
    """The result of reading an evidence stream."""

    events: tuple[Mapping[str, Any], ...]
    #: 1-based line numbers of lines that are not a valid event.
    malformed: tuple[int, ...]


class JsonLinesEvidenceRecorder:
    """Append-only JSON Lines recorder below the selected build output."""

    def __init__(self, output_dir: Path, run_id: str, clock: Clock) -> None:
        if not run_id:
            raise ContractError(
                FailureCategory.INVALID_INPUT, "evidence: run_id must be non-empty"
            )
        self._path = Path(output_dir) / EVIDENCE_FILE_NAME
        self._run_id = run_id
        self._clock = clock
        self._seq = self._count_existing()

    @property
    def path(self) -> Path:
        return self._path

    def record(self, kind: str, payload: Mapping[str, Any]) -> None:
        if kind not in EVENT_KINDS:
            raise ContractError(
                FailureCategory.INVALID_INPUT,
                f"evidence: unknown event kind '{kind}'",
                {"kind": kind},
            )
        clash = sorted(_RESERVED & set(payload))
        if clash:
            raise ContractError(
                FailureCategory.INVALID_INPUT,
                f"evidence: payload sets recorder-owned fields {clash}",
            )
        safe = apply_evidence_policy(payload, "payload")
        event = {
            **safe,
            "kind": kind,
            "run_id": self._run_id,
            "seq": self._seq + 1,
            "timestamp": self._clock(),
        }
        try:
            line = dumps(event)
        except (TypeError, ValueError) as exc:
            raise ContractError(
                FailureCategory.INVALID_INPUT,
                f"evidence: event is not serializable: {exc}",
            ) from exc
        self._append(line)
        self._seq += 1

    def _append(self, line: str) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._path.open("a", encoding="utf-8", newline="\n") as stream:
                if self._needs_separator():
                    stream.write("\n")
                stream.write(line + "\n")
                stream.flush()
                os.fsync(stream.fileno())
        except OSError as exc:
            raise ContractError(
                FailureCategory.EVIDENCE_WRITE_FAILED,
                f"evidence could not be written: {exc}",
                {"path": str(self._path)},
            ) from exc

    def _needs_separator(self) -> bool:
        """A prior run cut off mid-line: keep its fragment on a line of its own."""
        try:
            with self._path.open("rb") as stream:
                stream.seek(0, os.SEEK_END)
                if stream.tell() == 0:
                    return False
                stream.seek(-1, os.SEEK_END)
                return stream.read(1) != b"\n"
        except FileNotFoundError:
            return False

    def _count_existing(self) -> int:
        """Continue the sequence after the valid events already in the file."""
        if not self._path.is_file():
            return 0
        return len(read_events(self._path).events)


def read_events(path: Path) -> ReadEvents:
    """Parse an evidence stream, setting aside lines that are not valid events.

    A malformed prior line (truncated by a crash, hand-edited, not JSON, not an
    object, or without a known ``kind``) never stops the read and is never rewritten:
    it is reported by line number and the valid events around it keep their order.
    """
    events: list[Mapping[str, Any]] = []
    malformed: list[int] = []
    try:
        text = Path(path).read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = Path(path).read_bytes().decode("utf-8", errors="replace")
    for number, line in enumerate(_lines(text), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except ValueError:
            malformed.append(number)
            continue
        if isinstance(event, dict) and event.get("kind") in EVENT_KINDS:
            events.append(event)
        else:
            malformed.append(number)
    return ReadEvents(tuple(events), tuple(malformed))


def _lines(text: str) -> Iterator[str]:
    yield from text.split("\n")
