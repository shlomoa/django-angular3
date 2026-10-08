"""Bridge AppBuildSteps to the operator wrappers that run them.

Translation names a step with a Tool contract or a Skill name. The crosswalk of
``doc/ARCHITECTURE.md`` §3.6.4.1 maps those names to a concern key and an operator
wrapper; this module holds that table, selects the wrapper of a step through it and
resolves the options the wrapper needs from the project configuration and the ngdj
command mapping. Nothing here runs a command or writes a file, except
``stage_document``, which the executor calls right before a step needs the document.
"""

from __future__ import annotations

import re
import shutil
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Final

from .angular import (
    _COMMAND_BUILDERS,
    NGDJ_COLLECTION,
    AngularInvocation,
    build_ngdj_schematic_invocations,
)
from .command_translation import AppBuildStep
from .config import ProjectConfig
from .ngdj_command_mapping import CommandMapping, CommandMappingError
from .settings import DjangoAngularSettings

# The djng-owned part of the OpenUI document hand-off: an ngdj schematic reads the
# document through the workspace tree, so a document outside the workspace is copied
# here (``stage_document``) before the first step that needs it.
STAGED_DOCUMENT_DIRECTORY: Final = ".django-angular3"


class StepBridgeError(ValueError):
    """Raised when a step cannot be bridged to a wrapper or its options resolved."""


@dataclass(frozen=True)
class CrosswalkRow:
    """One row of the automation naming crosswalk (``ARCHITECTURE.md`` §3.6.4.1).

    An empty ``wrappers``, ``tools`` or ``skills`` is the table's ``—``: no canonical
    identifier exists in that layer.
    """

    concern_key: str
    wrappers: tuple[str, ...]
    tools: tuple[str, ...]
    skills: tuple[str, ...]


CROSSWALK: Final[tuple[CrosswalkRow, ...]] = (
    CrosswalkRow(
        "angular.workspace",
        ("ng_new", "ng_workspace", "ng_workspace_modify", "ng_workspace_delete"),
        ("angular_workspace_scaffold",),
        ("angular-workspace-foundation",),
    ),
    CrosswalkRow(
        "angular.app",
        ("ng_gen_app",),
        ("angular_app_scaffold",),
        ("angular-app-composition",),
    ),
    CrosswalkRow("angular.feature", (), ("ngdj_add_feature",), ()),
    CrosswalkRow(
        "angular.api-client",
        ("ng_openapi_gen",),
        ("angular_api_client_generate",),
        ("angular-api-integration",),
    ),
    CrosswalkRow(
        "angular.data-service",
        ("ng_data_service",),
        ("ngdj_add_data_service",),
        ("angular-data-service-composition",),
    ),
    CrosswalkRow(
        "angular.field-component",
        (),
        (),
        ("angular-field-component-composition",),
    ),
    CrosswalkRow("angular.form-field", (), (), ("angular-form-field-composition",)),
    CrosswalkRow(
        "angular.component",
        ("ng_component",),
        ("ngdj_add_component",),
        ("angular-component-composition",),
    ),
    CrosswalkRow(
        "angular.complex-component",
        ("ng_complex_component",),
        ("ngdj_add_complex_component",),
        ("angular-complex-component-composition",),
    ),
    CrosswalkRow(
        "angular.reactive-form",
        ("ng_reactive_form",),
        ("ngdj_add_reactive_form",),
        ("angular-reactive-form-composition",),
    ),
    CrosswalkRow(
        "angular.page",
        ("ng_page",),
        ("ngdj_add_page",),
        ("angular-page-composition",),
    ),
    CrosswalkRow("angular.tabs", (), ("ngdj_add_tabs",), ()),
    CrosswalkRow("angular.dialog", (), ("ngdj_add_dialog",), ()),
    CrosswalkRow("angular.stepper", (), ("ngdj_add_stepper",), ()),
    CrosswalkRow("angular.table", (), ("ngdj_add_table",), ()),
    CrosswalkRow(
        "contract.schema-export",
        ("export_schema",),
        ("openapi_schema_export",),
        (),
    ),
    CrosswalkRow("contract.schema-validate", (), ("validate_openapi_schema",), ()),
    CrosswalkRow("contract.schema-diff", (), ("oasdiff_diff", "oasdiff_changelog"), ()),
)

# A concern with several wrappers is run by the one that fits the step's operation.
_WRAPPER_BY_OPERATION: Final[dict[str, dict[str, str]]] = {
    "angular.workspace": {
        "create": "ng_workspace",
        "update": "ng_workspace_modify",
        "delete": "ng_workspace_delete",
    },
}

# The final gate is not a construction concern, so the crosswalk has no row for it.
# Until the terminal validation commands exist (``VERIFICATION_PLAN.md``), it builds
# the application, which checks the output of every step.
_GATE_WRAPPERS: Final[dict[str, str]] = {"last-check": "ng_build"}

# Wrapper option -> parameter of the ngdj command mapping, to check that the options
# a step carries are ones the command accepts.
_MAPPING_PARAMETERS: Final[dict[str, str]] = {
    "name": "name",
    "target_path": "path",
    "project": "project",
    "document": "document",
    "node_id": "nodeId",
    "resource": "name",
}

# Where a page or a complex component is generated, from the ngdj documentation of
# the commands (``--path`` is required and the mapping gives no default).
_PAGE_ROOT: Final = "src/app/features"
_COMPLEX_COMPONENT_ROOT: Final = "src/app/features"


def crosswalk_row(name_id: str) -> CrosswalkRow | None:
    """The row whose Tool contract or Skill name is ``name_id``, if any."""
    for row in CROSSWALK:
        if name_id in row.tools or name_id in row.skills:
            return row
    return None


def wrapper_for(step: AppBuildStep) -> tuple[str | None, str]:
    """The concern key and operator wrapper that run a step, through the crosswalk."""
    gate = _GATE_WRAPPERS.get(step.name_id)
    if gate is not None:
        return None, gate
    row = crosswalk_row(step.name_id)
    if row is None:
        raise StepBridgeError(
            f"{step.name_id} is not in the automation naming crosswalk."
        )
    if not row.wrappers and step.ngdj_command is not None:
        # No wrapper serves the concern: the step runs the ngdj command of the
        # mapping directly (``angular-django2:tabs``), so the mapping is the contract.
        return row.concern_key, f"{NGDJ_COLLECTION}:{step.ngdj_command}"
    if not row.wrappers:
        raise StepBridgeError(
            f"{step.name_id} ({row.concern_key}) has no operator wrapper."
        )
    by_operation = _WRAPPER_BY_OPERATION.get(row.concern_key)
    if by_operation is not None:
        wrapper = by_operation.get(step.change_op)
        if wrapper is None:
            raise StepBridgeError(
                f"No wrapper runs {step.change_op} for {row.concern_key} "
                f"({step.name_id})."
            )
        return row.concern_key, wrapper
    if len(row.wrappers) > 1:  # pragma: no cover - a crosswalk row needs a rule
        raise StepBridgeError(f"{row.concern_key} needs a wrapper rule.")
    return row.concern_key, row.wrappers[0]


def _schematic_of(command: str) -> str | None:
    """The ngdj schematic a step runs directly, or ``None`` for an operator wrapper."""
    collection, separator, schematic = command.partition(":")
    return schematic if separator and collection == NGDJ_COLLECTION else None


def dasherize(identifier: str) -> str:
    """The dasherized form of an OpenUI element id, as ngdj names the output."""
    spaced = re.sub(r"([a-z\d])([A-Z])", r"\1-\2", identifier)
    return re.sub(r"[\s_]+", "-", spaced).lower()


def workspace_document_path(project_config: ProjectConfig) -> str:
    """The workspace-relative path ngdj reads the OpenUI document from.

    A document that lies in the Angular workspace is read in place; any other is
    read from its staged copy (``stage_document``).
    """
    document = project_config.openui_specification
    try:
        return document.relative_to(project_config.angular_workspace).as_posix()
    except ValueError:
        return f"{STAGED_DOCUMENT_DIRECTORY}/{document.name}"


def stage_document(project_config: ProjectConfig) -> Path | None:
    """Copy the OpenUI document into the workspace when it lies outside; else ``None``.

    The workspace must already exist: the foundation steps create it, and
    creating it here would make ``ng new`` refuse the directory.
    """
    source = project_config.openui_specification
    workspace = project_config.angular_workspace
    target = workspace / workspace_document_path(project_config)
    if target == source:
        return None
    if not workspace.is_dir():
        raise StepBridgeError(
            f"Cannot stage the OpenUI document: the Angular workspace {workspace} "
            "does not exist."
        )
    if not source.is_file():
        raise StepBridgeError(f"OpenUI document not found: {source}.")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    return target


def resolve_steps(
    steps: tuple[AppBuildStep, ...],
    project_config: ProjectConfig,
    mapping: CommandMapping | None = None,
) -> tuple[AppBuildStep, ...]:
    """Bridge every step to its wrapper and resolve the options it needs.

    Pure: nothing is run or written. A step that has no wrapper, or whose options
    the ngdj command does not accept, raises ``StepBridgeError``.
    """
    return tuple(_resolve_step(step, project_config, mapping) for step in steps)


def _resolve_step(
    step: AppBuildStep, project_config: ProjectConfig, mapping: CommandMapping | None
) -> AppBuildStep:
    concern_key, wrapper = wrapper_for(step)
    if _schematic_of(wrapper) is None and wrapper not in _COMMAND_BUILDERS:
        raise StepBridgeError(
            f"{wrapper} ({step.name_id}) is an operator wrapper with no invocation "
            f"builder yet: {step.change_target}."
        )
    parameters, unresolved = _step_parameters(step, wrapper, project_config)
    if mapping is not None and step.ngdj_command is not None:
        _check_against_mapping(step, parameters, unresolved, mapping)
    return replace(
        step,
        concern_key=concern_key,
        command=wrapper,
        parameters=parameters,
        unresolved=unresolved,
    )


def _step_parameters(
    step: AppBuildStep, wrapper: str, project_config: ProjectConfig
) -> tuple[dict[str, object], tuple[str, ...]]:
    """The options of a wrapper for a step, and the required ones left unresolved."""
    project = project_config.project_name
    parameters: dict[str, object] = {}
    unresolved: tuple[str, ...] = ()

    if _schematic_of(wrapper) is not None:
        # name and path stay with the schematic's own defaults.
        if step.node_id is None:
            raise StepBridgeError(
                f"{step.name_id} needs the OpenUI element to compile: "
                f"{step.change_target}."
            )
        parameters["project"] = project
    elif wrapper == "ng_gen_app":
        parameters["app_name"] = project
    elif wrapper == "ng_data_service":
        # The resource identity rule across OpenAPI changes, ngdj data-service names
        # and OpenUI bindings is not decided (shlomoa/django-angular3#207).
        parameters["project"] = project
        unresolved = ("resource",)
    elif wrapper in {
        "ng_page",
        "ng_component",
        "ng_complex_component",
        "ng_reactive_form",
    }:
        if step.node_id is None:
            raise StepBridgeError(
                f"{step.name_id} needs the OpenUI element to compile: "
                f"{step.change_target}."
            )
        name = dasherize(step.node_id)
        parameters["name"] = name
        if wrapper == "ng_page":
            parameters["target_path"] = f"{_PAGE_ROOT}/{name}"
        elif wrapper == "ng_complex_component":
            if step.change_op != "create":
                raise StepBridgeError(
                    f"{step.name_id} supports only create from an OpenUI element, "
                    f"not {step.change_op}: {step.change_target}."
                )
            parameters["target_path"] = _COMPLEX_COMPONENT_ROOT
        parameters["project"] = project

    if step.node_id is not None and wrapper != "ng_data_service":
        parameters["document"] = workspace_document_path(project_config)
        parameters["node_id"] = step.node_id
    return parameters, unresolved


def _check_against_mapping(
    step: AppBuildStep,
    parameters: Mapping[str, object],
    unresolved: tuple[str, ...],
    mapping: CommandMapping,
) -> None:
    """Every option the step carries must be a parameter of its ngdj command."""
    command = step.ngdj_command or ""
    try:
        accepted = set(mapping.parameter_names(command))
    except CommandMappingError as exc:
        raise StepBridgeError(str(exc)) from exc
    for option in (*parameters, *unresolved):
        mapped = _MAPPING_PARAMETERS.get(option)
        if mapped is not None and mapped not in accepted:
            raise StepBridgeError(
                f"ngdj command {command} has no parameter {mapped} for the option "
                f"{option} of {step.command}: {step.change_target}."
            )


def build_invocations(
    step: AppBuildStep,
    project_config: ProjectConfig,
    settings: DjangoAngularSettings,
) -> list[AngularInvocation]:
    """Resolve the subprocess calls of a step's wrapper.

    May write the derived files a wrapper needs (``ng_openapi_gen`` writes its
    generator configuration), so a dry run must not call it.
    """
    if step.command is None:
        raise StepBridgeError(f"Step {step.name_id} has no resolved command.")
    if step.unresolved:
        raise StepBridgeError(
            f"{step.command} for {step.change_target} needs "
            f"{', '.join(step.unresolved)}, which is not resolved yet."
        )
    schematic = _schematic_of(step.command)
    if schematic is not None:
        return build_ngdj_schematic_invocations(
            project_config, settings, schematic=schematic, **step.parameters
        )
    builder = _COMMAND_BUILDERS.get(step.command)
    if builder is None:
        raise StepBridgeError(f"No invocation builder for {step.command}.")
    return builder(project_config, settings, **step.parameters)
