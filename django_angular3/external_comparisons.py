"""External OpenAPI and OpenUI comparison boundaries for the Change Model."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

from bin.compare_openui_json import compare as compare_openui_json

from .changes import Change, ChangeDomain, ChangeEvidence, ChangeOperation
from .documents import DocumentError, load_document
from .tools import ensure_oasdiff
from .validation import validate_openui_document


class ExternalComparisonError(ValueError):
    """Raised when a comparison tool input or result is unsupported."""


def run_oasdiff_diff(reference: Path, candidate: Path) -> dict[str, object]:
    """Run oasdiff's JSON diff and return its validated raw result.

    OpenAPI semantic record translation remains owned by the OpenAPI evaluator.
    """
    executable = ensure_oasdiff()
    result = subprocess.run(
        [executable, "diff", str(reference), str(candidate), "--format", "json"],
        capture_output=True,
        text=True,
    )
    if result.returncode:
        message = (result.stderr or result.stdout).strip()
        raise ExternalComparisonError(
            f"oasdiff failed with exit code {result.returncode}: {message}"
        )
    if not result.stdout.strip():
        return {}

    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ExternalComparisonError("oasdiff did not produce valid JSON.") from exc
    if not isinstance(output, Mapping) or not all(
        isinstance(key, str) for key in output
    ):
        raise ExternalComparisonError("oasdiff JSON output must be an object.")
    return dict(cast(Mapping[str, object], output))


def compare_openui_files(reference: Path, candidate: Path) -> tuple[Change, ...]:
    """Load, validate, and compare OpenUI JSON files through openui-spec."""
    reference_document = _load_openui_document(reference)
    candidate_document = _load_openui_document(candidate)
    changelog = compare_openui_json(reference_document, candidate_document)
    return translate_openui_changelog(changelog, source=str(candidate))


def translate_openui_changelog(
    changelog: Mapping[str, object], *, source: str
) -> tuple[Change, ...]:
    """Translate validated upstream OpenUI changelog records into Changes."""
    expected_keys = {"remove", "add", "change"}
    if set(changelog) != expected_keys:
        raise ExternalComparisonError(
            "OpenUI comparison output must contain only remove, add, and change."
        )

    changes: list[Change] = []
    for category, operation, before_key, after_key in (
        ("remove", ChangeOperation.DELETE, "reference", None),
        ("add", ChangeOperation.CREATE, None, "new"),
        ("change", ChangeOperation.UPDATE, "reference", "new"),
    ):
        entries = changelog[category]
        if not isinstance(entries, Sequence) or isinstance(entries, str):
            raise ExternalComparisonError(
                f"OpenUI comparison output '{category}' must be a list."
            )
        for entry in entries:
            changes.append(
                _openui_change(
                    category,
                    operation,
                    _validated_openui_entry(entry, category, before_key, after_key),
                    before_key,
                    after_key,
                    source,
                )
            )
    return tuple(changes)


def _load_openui_document(path: Path) -> object:
    if path.suffix.lower() != ".json":
        raise ExternalComparisonError("OpenUI comparison inputs must be JSON files.")
    try:
        document = load_document(path)
    except DocumentError as exc:
        raise ExternalComparisonError(str(exc)) from exc
    errors = validate_openui_document(document)
    if errors:
        raise ExternalComparisonError("Invalid OpenUI document: " + "; ".join(errors))
    return document


def _validated_openui_entry(
    entry: object,
    category: str,
    before_key: str | None,
    after_key: str | None,
) -> Mapping[str, object]:
    if not isinstance(entry, Mapping):
        raise ExternalComparisonError(
            f"OpenUI comparison '{category}' entries must be objects."
        )
    record = cast(Mapping[str, object], entry)
    expected_keys = {"path"}
    if before_key is not None:
        expected_keys.add(before_key)
    if after_key is not None:
        expected_keys.add(after_key)
    if set(record) != expected_keys or not isinstance(record.get("path"), str):
        raise ExternalComparisonError(
            f"OpenUI comparison '{category}' entry has an unsupported shape."
        )
    return record


def _openui_change(
    category: str,
    operation: ChangeOperation,
    entry: Mapping[str, object],
    before_key: str | None,
    after_key: str | None,
    source: str,
) -> Change:
    path = cast(str, entry["path"])
    before = None if before_key is None else entry[before_key]
    after = None if after_key is None else entry[after_key]
    return Change(
        domain=ChangeDomain.OPENUI,
        subject=f"openui:{path}",
        path=path,
        operation=operation,
        before=before,
        after=after,
        evidence=(ChangeEvidence(source, location=path, fragment=dict(entry)),),
    )
