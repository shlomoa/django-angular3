"""The executable Tool catalog: names, structured inputs, outputs and references.

The normative contracts are in ``doc/contracts/TOOL_CONTRACTS.md``. This table is
their executable form; ``tests/test_automation_tools.py`` compares it with the
contract tables, so a drift in either is a failing test. Standard library only.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Final

from .contracts import ContractError, FailureCategory

# Input kinds. ``enum:a|b`` is a string from the listed values.
STRING: Final = "string"
PATH: Final = "path"  # a string naming a path
BOOL: Final = "boolean"
OBJECT: Final = "object"
STRING_OR_LIST: Final = "string_or_list"
_KEBAB = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")


@dataclass(frozen=True)
class InputSpec:
    name: str
    required: bool
    kind: str = STRING


@dataclass(frozen=True)
class ToolSpec:
    """One catalogued Tool: its inputs, output keys and implementation reference."""

    name: str
    inputs: tuple[InputSpec, ...]
    outputs: tuple[str, ...]
    #: ``module:attribute`` of the function that implements the Tool.
    implementation: str

    def input_names(self) -> tuple[str, ...]:
        return tuple(spec.name for spec in self.inputs)


def _in(name: str, kind: str = STRING, *, required: bool = False) -> InputSpec:
    return InputSpec(name, required, kind)


def _enum(*values: str) -> str:
    return "enum:" + "|".join(values)


_DRY = _in("dry_run", BOOL)
_PROJECT = _in("project")
_DOCUMENT = _in("document", PATH)
_NODE = _in("node_id")
_IMPL = "django_angular3.automation.tools"

_WIDGET_INPUTS = (
    _in("document", PATH, required=True),
    _NODE,
    _in("name"),
    _in("path", PATH),
    _PROJECT,
    _DRY,
)
_WIDGET_OUTPUTS = ("generated_files", "command")

CATALOG: Final[Mapping[str, ToolSpec]] = {
    spec.name: spec
    for spec in (
        ToolSpec(
            "openapi_schema_export",
            (_in("format", _enum("json", "yaml")), _DRY),
            (
                "destination",
                "previous_path",
                "format",
                "bytes_written",
                "schema_changed",
            ),
            f"{_IMPL}:openapi_schema_export",
        ),
        ToolSpec(
            "validate_openapi_schema",
            (
                _in("schema", PATH, required=True),
                _in("format", _enum("json", "yaml", "auto")),
                _in("ruleset", PATH),
            ),
            ("valid", "errors", "warnings", "openapi_version", "resource_count"),
            f"{_IMPL}:validate_openapi_schema",
        ),
        ToolSpec(
            "oasdiff_diff",
            (
                _in("current_schema", PATH, required=True),
                _in("previous_schema", PATH, required=True),
                _in("report_path", PATH),
                _in("format", _enum("json", "yaml", "text")),
            ),
            ("schema_changed", "changes", "affected_resources", "report_path"),
            f"{_IMPL}:oasdiff_diff",
        ),
        ToolSpec(
            "angular_api_client_generate",
            (_in("schema", PATH), _DRY),
            (
                "output_dir",
                "generated_files",
                "client_count",
                "generator_version",
                "command",
            ),
            f"{_IMPL}:angular_api_client_generate",
        ),
        ToolSpec(
            "angular_workspace_scaffold",
            (_DOCUMENT, _DRY),
            ("workspace_path", "package_manager", "angular_version", "command"),
            f"{_IMPL}:angular_workspace_scaffold",
        ),
        ToolSpec(
            "angular_app_scaffold",
            (_DOCUMENT, _NODE, _DRY),
            ("app_path", "app_name", "command"),
            f"{_IMPL}:angular_app_scaffold",
        ),
        ToolSpec(
            "ngdj_add_feature",
            (
                _in("name", required=True),
                _in("path", PATH),
                _PROJECT,
                _in("page_name"),
                _in("route_path"),
                _in("register_route", BOOL),
                _DRY,
            ),
            (
                "feature_path",
                "page_component_path",
                "feature_routes_path",
                "app_routes_path",
                "generated_files",
                "commands",
            ),
            f"{_IMPL}:ngdj_add_feature",
        ),
        ToolSpec(
            "ngdj_add_component",
            (
                _in("name", required=True),
                _in("path", PATH),
                _PROJECT,
                _DOCUMENT,
                _NODE,
                _DRY,
            ),
            (
                "component_path",
                "component_class",
                "selector",
                "generated_files",
                "command",
            ),
            f"{_IMPL}:ngdj_add_component",
        ),
        ToolSpec(
            "ngdj_run_schematic",
            (_in("schematic", required=True), _in("options", OBJECT), _PROJECT, _DRY),
            ("schematic", "generated_files", "command", "warnings"),
            f"{_IMPL}:ngdj_run_schematic",
        ),
        ToolSpec(
            "oasdiff_changelog",
            (
                _in("current_schema", PATH, required=True),
                _in("previous_schema", PATH, required=True),
                _in("output_path", PATH),
                _in("format", _enum("markdown", "html")),
                _DRY,
            ),
            ("changelog_path", "format", "schema_changed", "command"),
            f"{_IMPL}:oasdiff_changelog",
        ),
        ToolSpec(
            "ngdj_add_page",
            (
                _in("name", required=True),
                _in("path", PATH, required=True),
                _PROJECT,
                _in("route_path"),
                _in("access", _enum("public", "protected")),
                _in("auth_guard"),
                _in("navigation_label"),
                _in("navigation_icon"),
                _DOCUMENT,
                _NODE,
                _DRY,
            ),
            ("page_path", "generated_files", "command"),
            f"{_IMPL}:ngdj_add_page",
        ),
        ToolSpec(
            "ngdj_add_reactive_form",
            (
                _in("name", required=True),
                _DOCUMENT,
                _NODE,
                _in("definition", PATH),
                _in("path", PATH),
                _PROJECT,
                _in("primitives_path", PATH),
                _DRY,
            ),
            ("form_path", "generated_files", "command"),
            f"{_IMPL}:ngdj_add_reactive_form",
        ),
        ToolSpec(
            "ngdj_add_complex_component",
            (
                _in("name", required=True),
                _in("path", PATH, required=True),
                _in("features", STRING_OR_LIST, required=True),
                _in("mode", _enum("create", "modify")),
                _in("confirm", BOOL),
                _PROJECT,
                _DOCUMENT,
                _NODE,
                _DRY,
            ),
            ("component_path", "generated_files", "command"),
            f"{_IMPL}:ngdj_add_complex_component",
        ),
        ToolSpec(
            "ngdj_add_data_service",
            (
                _in("resource", required=True),
                _PROJECT,
                _in("api_service"),
                _in("path", PATH),
                _DRY,
            ),
            ("service_path", "generated_files", "command"),
            f"{_IMPL}:ngdj_add_data_service",
        ),
        ToolSpec(
            "ngdj_add_tabs", _WIDGET_INPUTS, _WIDGET_OUTPUTS, f"{_IMPL}:ngdj_add_tabs"
        ),
        ToolSpec(
            "ngdj_add_dialog",
            _WIDGET_INPUTS,
            _WIDGET_OUTPUTS,
            f"{_IMPL}:ngdj_add_dialog",
        ),
        ToolSpec(
            "ngdj_add_stepper",
            _WIDGET_INPUTS,
            _WIDGET_OUTPUTS,
            f"{_IMPL}:ngdj_add_stepper",
        ),
        ToolSpec(
            "ngdj_add_table",
            _WIDGET_INPUTS,
            _WIDGET_OUTPUTS,
            f"{_IMPL}:ngdj_add_table",
        ),
    )
}


def invalid(tool: str, message: str, **details: Any) -> ContractError:
    return ContractError(
        FailureCategory.INVALID_INPUT, f"{tool}: {message}", {"tool": tool, **details}
    )


def validate_inputs(spec: ToolSpec, inputs: Mapping[str, Any]) -> dict[str, Any]:
    """Check ``inputs`` against the contract; returns a copy with only known keys.

    Raises ``ContractError`` (``invalid_input``) for a missing required key, an unknown
    key or a value of the wrong type. Defaults are applied by the implementations,
    not here, so an absent optional key stays absent.
    """
    if not isinstance(inputs, Mapping):
        raise invalid(spec.name, "inputs must be an object")
    known = {item.name: item for item in spec.inputs}
    unknown = sorted(set(inputs) - set(known))
    if unknown:
        raise invalid(spec.name, f"unknown inputs {unknown}", field=unknown[0])
    for item in spec.inputs:
        if item.required and item.name not in inputs:
            raise invalid(
                spec.name, f"missing required input '{item.name}'", field=item.name
            )
    checked: dict[str, Any] = {}
    for name, value in inputs.items():
        if value is None:
            continue
        _check_kind(spec.name, known[name], value)
        checked[name] = value
    return checked


def _check_kind(tool: str, item: InputSpec, value: Any) -> None:
    kind = item.kind
    ok: bool
    if kind in (STRING, PATH):
        ok = isinstance(value, str) and bool(value.strip())
    elif kind == BOOL:
        ok = isinstance(value, bool)
    elif kind == OBJECT:
        ok = isinstance(value, Mapping)
    elif kind == STRING_OR_LIST:
        ok = (isinstance(value, str) and bool(value.strip())) or (
            isinstance(value, (list, tuple))
            and bool(value)
            and all(isinstance(entry, str) and entry for entry in value)
        )
    elif kind.startswith("enum:"):
        ok = isinstance(value, str) and value in kind[5:].split("|")
    else:  # pragma: no cover - a catalog bug
        raise AssertionError(f"unknown input kind {kind}")
    if not ok:
        raise invalid(
            tool, f"input '{item.name}' must be of type {kind}", field=item.name
        )


def require_kebab_case(tool: str, field: str, value: str) -> None:
    if not _KEBAB.fullmatch(value):
        raise invalid(tool, f"'{field}' must be kebab-case, not {value!r}", field=field)
