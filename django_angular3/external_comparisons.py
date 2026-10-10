"""External OpenAPI and OpenUI comparison boundaries for the Change Model."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from openui_spec import compare as compare_openui_spec

from .changes import Change, ChangeDomain, ChangeEvidence, ChangeOperation
from .command_execution import run_command
from .documents import DocumentError, load_document
from .tools import OasdiffUnavailableError, ensure_oasdiff
from .validation import validate_openui_document


class ExternalComparisonError(ValueError):
    """Raised when a comparison tool input or result is unsupported."""


_ELEMENT_EVIDENCE_KEY = "openuiElement"


@dataclass(frozen=True)
class OpenUiElement:
    """An OpenUI element that encloses a changed value, as the Change records it.

    ``path`` is the element's JSON Pointer in the document it was read from: the
    candidate for a ``create`` or ``update``, the reference for a ``delete``. ``type``
    is the element's type in that same document.
    """

    id: str
    type: str
    path: str


def run_oasdiff_diff(reference: Path, candidate: Path) -> dict[str, object]:
    """Run oasdiff's JSON diff and return its validated raw result.

    OpenAPI semantic record translation remains owned by the OpenAPI evaluator.
    """
    try:
        executable = ensure_oasdiff()
    except OasdiffUnavailableError as exc:
        raise ExternalComparisonError(str(exc)) from exc
    result = run_command(
        [executable, "diff", str(reference), str(candidate), "--format", "json"],
        check=False,
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
    changelog = compare_openui_spec(reference_document, candidate_document)
    return translate_openui_changelog(
        changelog,
        source=str(candidate),
        reference=reference_document,
        candidate=candidate_document,
    )


def translate_openui_changelog(
    changelog: Mapping[str, object],
    *,
    source: str,
    reference: object = None,
    candidate: object = None,
) -> tuple[Change, ...]:
    """Translate validated upstream OpenUI changelog records into Changes.

    With the ``reference`` and ``candidate`` documents the changelog was computed
    from, each Change also records the elements that enclose its path as evidence
    (see ``openui_change_elements``). Without them the Changes carry no element
    evidence.
    """
    if (reference is None) != (candidate is None):
        raise ValueError(
            "Pass both the reference and the candidate document, or neither."
        )
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
                    # A removed element exists only in the reference document.
                    reference if operation is ChangeOperation.DELETE else candidate,
                )
            )
    return tuple(changes)


def openui_change_elements(change: Change) -> tuple[OpenUiElement, ...]:
    """The elements that enclose an OpenUI Change's path, root element first.

    The last element is the nearest one: the element the path names, or the one that
    owns the attribute, child list or member it names. The chain is empty for a Change
    derived without documents. Resolving an embedded element to the root element that
    compiles it needs the ngdj command mapping and belongs to command translation.
    """
    elements: list[OpenUiElement] = []
    for record in change.evidence:
        fragment = record.fragment
        if isinstance(fragment, Mapping) and _ELEMENT_EVIDENCE_KEY in fragment:
            element = cast(Mapping[str, str], fragment[_ELEMENT_EVIDENCE_KEY])
            elements.append(
                OpenUiElement(
                    id=element["id"],
                    type=element["type"],
                    path=record.location or "",
                )
            )
    return tuple(elements)


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
    document: object = None,
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
        evidence=(
            ChangeEvidence(source, location=path, fragment=dict(entry)),
            *_element_evidence(source, document, path),
        ),
    )


def _element_evidence(
    source: str, document: object, path: str
) -> tuple[ChangeEvidence, ...]:
    """One evidence record per element enclosing ``path``, root element first."""
    if document is None:
        return ()
    return tuple(
        ChangeEvidence(
            source,
            # The root element's pointer is empty, which evidence cannot hold.
            location=element.path or None,
            fragment={_ELEMENT_EVIDENCE_KEY: {"id": element.id, "type": element.type}},
        )
        for element in _enclosing_elements(document, path)
    )


def _enclosing_elements(document: object, path: str) -> tuple[OpenUiElement, ...]:
    """Walk an upstream comparison path and list the elements it passes through.

    The path is a JSON Pointer whose segments are member names and, inside a
    ``children`` list, element ids (``spec/tooling/comparison.md``, Paths). The walk
    stops at the first segment that is not an element id: a member name such as
    ``attrs`` or ``type``, or a whole ``children`` list.
    """
    if not isinstance(document, Mapping) or not path.startswith("/"):
        raise ExternalComparisonError(f"Cannot resolve OpenUI path {path!r}.")
    raw_segments = path.split("/")[1:]
    node = cast(Mapping[str, object], document)
    elements = [_element(node, "")]
    pointer = ""
    index = 0
    while index + 1 < len(raw_segments) and raw_segments[index] == "children":
        child_id = _unescape_pointer_segment(raw_segments[index + 1])
        child = _child_by_id(node, child_id)
        if child is None:
            raise ExternalComparisonError(
                f"OpenUI path {path!r} names no element {child_id!r}."
            )
        pointer += f"/children/{raw_segments[index + 1]}"
        node = cast(Mapping[str, object], child)
        elements.append(_element(node, pointer))
        index += 2
    return tuple(elements)


def _child_by_id(node: Mapping[str, object], child_id: str) -> object:
    children = node.get("children")
    if isinstance(children, Sequence) and not isinstance(children, str):
        for item in children:
            if isinstance(item, Mapping) and item.get("id") == child_id:
                return item
    return None


def _element(node: Mapping[str, object], pointer: str) -> OpenUiElement:
    element_id, element_type = node.get("id"), node.get("type")
    if not isinstance(element_id, str) or not isinstance(element_type, str):
        raise ExternalComparisonError(
            f"OpenUI element at {pointer or '/'!r} has no string id and type."
        )
    return OpenUiElement(element_id, element_type, pointer)


def _unescape_pointer_segment(segment: str) -> str:
    return segment.replace("~1", "/").replace("~0", "~")
