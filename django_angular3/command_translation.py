"""Deterministically translate Changes into an ordered list of AppBuildSteps."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from typing import Final

from .changes import Change, ChangeDomain, ChangeOperation
from .external_comparisons import OpenUiElement, openui_change_elements
from .ngdj_command_mapping import CommandMapping


class CommandTranslationError(ValueError):
    """Raised when no documented command mapping exists for a Change."""


@dataclass(frozen=True)
class AppBuildStep:
    """One ordered step of the app build: a construction command or gate.

    A step is produced from one atomic Change (a single Change can yield
    several steps, for example an OpenAPI change yields three), except for the
    final ``last-check`` gate, which is appended once for the whole
    change set. A step only describes what should run; it does not execute
    anything. Translation leaves the command and its parameters empty, because
    they depend on the project configuration: ``step_bridge.resolve_steps`` fills
    ``concern_key``, ``command`` and ``parameters`` (see below). Identical steps
    from different Changes are not merged, except
    that project-config steps are merged into one step that lists every subject
    (see ``_merge_project_steps``).

    Steps are sorted by ``exec_order``, then ``change_op``, ``change_domain``,
    ``name_id`` and ``change_target`` (see ``_step_sort_key``) to keep the order
    deterministic.

    Attributes:
        name_id: Identifier of the construction command, or ``last-check`` for
            the final gate. OpenUI steps use the TOOL contract name (for
            example ``ngdj_add_page``). The project-config and static-config
            foundation steps keep the Skill-layer names
            (``angular-workspace-foundation``) until Tool contracts exist for
            modifying a workspace or application; the schema export and the
            client generation of a static setting use their Tool names. See
            ``doc/ARCHITECTURE.md`` §3.6.4 for the naming layers.
        exec_order: Pipeline stage number.
            0 schema export, 1 workspace foundation, 2 app composition,
            3 API integration, 4 data services, 7 components, 8 complex
            components, 9 reactive forms, 10 pages, 12 last validation.
            Values 5, 6 and 11 are
            currently unused: a navigation change is an update of the
            ``Application``, which is stage 2.
        change_op: What the command should do. One of the ``ChangeOperation``
            values (``create``, ``update``, ``move``, ``delete``) copied from
            the originating Change, or ``validate`` for the last gate.
            Breaks ties between steps with the same ``exec_order``:
            then update and move, then create, then validate.
        change_reason: Human-readable explanation of which Change required
            the step, for output and debug logs.
        change_target: Identifier of the thing the Change affects (for example
            ``openui:/children/home`` or ``path:/api/items``), or ``changeset``
            for the last gate.
        change_domain: ``ChangeDomain`` the originating Change belongs to, or
            ``None`` for the last gate, which covers the whole change set.
            Breaks ties after ``change_op``:
            OpenUI, with all other domains and ``None`` sorting before both.
        node_id: ``id`` of the OpenUI element the command compiles, for an
            OpenUI step, otherwise ``None``. The step's ``--node-id``.
        ngdj_command: Name of the ngdj command of the upstream mapping that the
            step runs (for example ``page``), when translation selected one from
            the mapping; otherwise ``None``.
        concern_key: Concern key of the crosswalk row (``ARCHITECTURE.md``
            §3.6.4.1) the step belongs to, for example ``angular.page``. Set by
            ``step_bridge.resolve_steps``; ``None`` for the ``last-check`` gate
            and before resolution.
        command: Operator wrapper identifier (for example ``ng_page``) that runs
            the step, chosen through the crosswalk. Set by
            ``step_bridge.resolve_steps``; ``None`` before resolution.
        parameters: The wrapper options resolved for the step, by the wrapper's
            option name (for example ``name``, ``target_path``, ``project``,
            ``document`` and ``node_id``). Derived from the project
            configuration and the mapping; no site identifier is read from
            ngdj. Empty before resolution.
        unresolved: Names of required wrapper options that cannot be resolved
            yet (for example the ``resource`` of a data service, whose identity
            rule is open). A dry run lists them; a real run refuses to start
            while any step has one.
    """

    name_id: str
    exec_order: int
    change_op: str
    change_reason: str
    change_target: str
    change_domain: ChangeDomain | None
    node_id: str | None = None
    ngdj_command: str | None = None
    concern_key: str | None = None
    command: str | None = None
    parameters: Mapping[str, object] = field(default_factory=dict, hash=False)
    unresolved: tuple[str, ...] = ()


def translate_changes(
    changes: tuple[Change, ...], mapping: CommandMapping | None = None
) -> tuple[AppBuildStep, ...]:
    """Translate supported changes into ordered commands and a last gate.

    This only derives the steps: it neither invokes wrappers nor changes the
    generated-app workspace. Every unsupported semantic subject is rejected.
    ``mapping`` is the ngdj command mapping; OpenUI and OpenAPI Changes need it.
    An empty change list means nothing changed and gives no steps, not even
    the validation gate.
    """
    if not changes:
        return ()
    steps = _merge_project_steps(
        [step for change in changes for step in _change_steps(change, mapping)]
    )
    steps.append(
        AppBuildStep(
            name_id="last-check",
            exec_order=12,
            change_op="validate",
            change_reason="Validate the outputs of all the steps.",
            change_target="changeset",
            change_domain=None,
        )
    )
    return tuple(sorted(steps, key=_step_sort_key))


def _merge_project_steps(steps: list[AppBuildStep]) -> list[AppBuildStep]:
    """Collapse project-level steps that several project-config Changes require.

    Project-config steps carry no per-target options, so two of them with the
    same command and operation are the same command. A first run creates every
    project-config subject, and ``project.name`` and ``artifacts.angularWorkspace``
    both need the workspace and application foundation commands; running those
    twice would fail on the second run. The merged step lists every subject.
    Steps of other domains are never merged: their targets select different
    work (for example one page each).
    """
    targets: dict[tuple[str, str], list[str]] = {}
    merged: list[AppBuildStep] = []
    for step in steps:
        if step.change_domain is not ChangeDomain.PROJECT_CONFIG:
            merged.append(step)
            continue
        key = (step.name_id, step.change_op)
        if key in targets:
            targets[key].append(step.change_target)
        else:
            targets[key] = [step.change_target]
            merged.append(step)
    return [
        _merged_project_step(step, targets[(step.name_id, step.change_op)])
        if step.change_domain is ChangeDomain.PROJECT_CONFIG
        else step
        for step in merged
    ]


def _merged_project_step(step: AppBuildStep, subjects: list[str]) -> AppBuildStep:
    if len(subjects) == 1:
        return step
    joined = ", ".join(sorted(subjects))
    return replace(
        step,
        change_reason=f"Required by project_config {step.change_op}: {joined}.",
        change_target=joined,
    )


ChangeTranslator = Callable[[Change], tuple[AppBuildStep, ...]]


def _not_implemented(change: Change) -> tuple[AppBuildStep, ...]:
    """Placeholder for a mapped name whose translation is not implemented yet."""
    raise CommandTranslationError(
        f"Translation not implemented for {change.domain.value} "
        f"{change.operation.value}: {change.subject}."
    )


_CONFIG_OPERATIONS: Final = (ChangeOperation.CREATE, ChangeOperation.UPDATE)


def _require_create_or_update(change: Change) -> None:
    """Reject operations without a documented configuration translation.

    A configuration value is created (no baseline, or a new setting) or
    updated. ``delete`` and ``move`` have no translation, so they fail
    explicitly instead of being treated as no work.
    """
    if change.operation not in _CONFIG_OPERATIONS:
        raise CommandTranslationError(
            f"Unsupported Change operation: {change.domain.value} "
            f"{change.operation.value}: {change.subject}."
        )


def _translate_project_foundation(change: Change) -> tuple[AppBuildStep, ...]:
    """Project identity and workspace location: workspace, then application.

    ``project.name`` names the workspace and the Angular application, and
    ``artifacts.angularWorkspace`` is where both live, so a change to either
    needs the project-level foundation commands (``APP_BUILDER_REQUIREMENTS.md``
    Change-to-command mapping).
    """
    _require_create_or_update(change)
    return (
        _change_step(1, "angular-workspace-foundation", change),
        _change_step(2, "angular-app-composition", change),
    )


def _translate_project_selector(change: Change) -> tuple[AppBuildStep, ...]:
    """OpenAPI and OpenUI source selectors need no construction command.

    A selector change is a separate fact from a change in the selected content
    (``CHANGE_MODEL_CONTRACTS.md`` §2.2): the openapi and openui domains
    compare the selected documents and drive their own commands, and the final
    ``last-check`` gate validates the newly selected source.
    """
    _require_create_or_update(change)
    return ()


# Per-domain maps from a Change subject to the translator that returns the
# ordered steps for that Change. The subject must match a key exactly.
PROJECT_CONFIG_CHANGE_TRANSLATORS: Final[dict[str, ChangeTranslator]] = {
    "project.name": _translate_project_foundation,
    "artifacts.angularWorkspace": _translate_project_foundation,
    "artifacts.openapiSchema": _translate_project_selector,
    "artifacts.openuiSpecification": _translate_project_selector,
}


DOMAIN_CHANGE_TRANSLATORS: Final[dict[ChangeDomain, dict[str, ChangeTranslator]]] = {
    ChangeDomain.PROJECT_CONFIG: PROJECT_CONFIG_CHANGE_TRANSLATORS,
}


@dataclass(frozen=True)
class _StaticConfigRule:
    """The steps a static-configuration subject, and any subject below it, needs.

    ``steps`` are ``(exec_order, name_id)`` pairs; none means the setting changes no
    construction output, so only the final validation gate follows.
    """

    subject: str
    steps: tuple[tuple[int, str], ...]


# Which command consumes which setting of ``django-angular3.json``
# (``SPECIFICATIONS.md`` §2.1). A workspace setting is reapplied by the workspace
# modification wrapper, as the scenario specification shows for
# ``angular.workspace.style``. The Skill-layer names are those of the project-config
# foundation steps; the schema export and the client generation have Tool contracts.
_STATIC_CONFIG_RULES: Final[tuple[_StaticConfigRule, ...]] = (
    _StaticConfigRule("drfSpectacular.settings", ((0, "openapi_schema_export"),)),
    _StaticConfigRule("angular.workspace", ((1, "angular-workspace-foundation"),)),
    _StaticConfigRule("tool.ngAddPackage", ((1, "angular-workspace-foundation"),)),
    _StaticConfigRule("angular.application", ((2, "angular-app-composition"),)),
    _StaticConfigRule("ngOpenApiGen", ((3, "angular_api_client_generate"),)),
    # Read only by the build gate, the diff tool and the executable lookup.
    _StaticConfigRule("angular.build", ()),
    _StaticConfigRule("oasdiff", ()),
    _StaticConfigRule("tool.executables", ()),
)


def _translate_static_config_change(change: Change) -> tuple[AppBuildStep, ...]:
    for rule in _STATIC_CONFIG_RULES:
        if change.subject == rule.subject or change.subject.startswith(
            rule.subject + "."
        ):
            _require_create_or_update(change)
            return tuple(
                _change_step(order, name, change) for order, name in rule.steps
            )
    raise CommandTranslationError(f"Unsupported Change subject: {change.subject}.")


@dataclass(frozen=True)
class _OpenUiTool:
    """The djng Tool contract and pipeline stage that run one ngdj command."""

    name: str
    exec_order: int


# The ngdj commands djng has a Tool contract for (``TOOL_CONTRACTS.md``), keyed by
# the command name of the upstream mapping. Which command compiles which OpenUI
# node type, and which operations it supports, is read from that mapping.
_OPENUI_TOOLS: Final[dict[str, _OpenUiTool]] = {
    "material-app": _OpenUiTool("angular_app_scaffold", 2),
    "component": _OpenUiTool("ngdj_add_component", 7),
    "complex-component": _OpenUiTool("ngdj_add_complex_component", 8),
    "reactive-form": _OpenUiTool("ngdj_add_reactive_form", 9),
    "page": _OpenUiTool("ngdj_add_page", 10),
    # Standalone widgets and containers that compile their own children. Stage 6 puts
    # them before a page, which will embed them once the mapping allows it.
    "tabs": _OpenUiTool("ngdj_add_tabs", 6),
    "dialog": _OpenUiTool("ngdj_add_dialog", 6),
    "stepper": _OpenUiTool("ngdj_add_stepper", 6),
    "table": _OpenUiTool("ngdj_add_table", 6),
}


def _has_overlay_child(element: object) -> bool:
    children = element.get("children") if isinstance(element, Mapping) else None
    return isinstance(children, tuple) and any(
        isinstance(child, Mapping) and child.get("type") == "OverlayContainers"
        for child in children
    )


# The mapping gives a command that compiles a node type under a prose condition
# (``when``). djng decides those conditions here, from the element: ngdj compiles
# a container with an overlay child with ``complex-component``, and djng generates
# the application with ``material-app`` (``ng_gen_app``).
_COMMAND_CONDITIONS: Final[dict[tuple[str, str], Callable[[object], bool]]] = {
    ("SurfaceContainers", "complex-component"): _has_overlay_child,
    ("Application", "material-app"): lambda _element: True,
}


def _change_steps(
    change: Change, mapping: CommandMapping | None = None
) -> tuple[AppBuildStep, ...]:
    if change.domain is ChangeDomain.OPENUI:
        return _translate_openui_change(change, mapping)
    if change.domain is ChangeDomain.OPENAPI:
        return _translate_openapi_change(change, mapping)
    if change.domain is ChangeDomain.STATIC_CONFIG:
        return _translate_static_config_change(change)
    translators = DOMAIN_CHANGE_TRANSLATORS.get(change.domain)
    if translators is None:
        raise CommandTranslationError(f"Unsupported Change domain: {change.domain}.")
    if change.subject not in translators:
        raise CommandTranslationError(f"Unsupported Change subject: {change.subject}.")
    return translators[change.subject](change)


_OPENAPI_SUBJECT_KINDS: Final = ("path", "operation", "schema")
_DATA_SERVICE_COMMAND: Final = "data-service"


def _translate_openapi_change(
    change: Change, mapping: CommandMapping | None
) -> tuple[AppBuildStep, ...]:
    """Select the client regeneration and data service an OpenAPI Change needs.

    Every change regenerates the typed client from the changed schema. A new path
    (a new resource) also gets its data service. A change to an operation, or to
    a path or schema that already has services depending on it, would have to
    update or delete data services, and the upstream mapping says ngdj cannot
    (``data-service`` is create-only), so it fails explicitly with the mapping's
    reason. The dependent OpenUI commands come from the OpenUI Changes, not from
    here.
    """
    kind, _, _ = change.subject.partition(":")
    if kind not in _OPENAPI_SUBJECT_KINDS:
        raise CommandTranslationError(f"Unsupported Change subject: {change.subject}.")
    if mapping is None:
        raise CommandTranslationError(
            "OpenAPI Change translation needs the ngdj command mapping."
        )

    client = AppBuildStep(
        name_id="angular_api_client_generate",
        exec_order=3,
        change_op=change.operation.value,
        change_reason=(
            f"Required by openapi {change.operation.value}: {change.subject}. "
            "The typed client is regenerated from the changed schema."
        ),
        change_target=change.subject,
        change_domain=change.domain,
    )
    if kind == "schema" and change.operation is ChangeOperation.CREATE:
        return (client,)

    # A path is a resource: its creation creates its data service. A change to
    # an operation modifies the service of the path it belongs to, and a schema
    # change modifies the services that use it.
    operation = (
        ChangeOperation.UPDATE if kind == "operation" else change.operation
    ).value
    status = mapping.command_operation_status(_DATA_SERVICE_COMMAND, operation)
    if status.status != "supported":
        subject = (
            "the data services that depend on"
            if kind == "schema"
            else "the data service of"
        )
        detail = f": {status.reason}" if status.reason else ""
        gap = f" ({status.gap})" if status.gap else ""
        raise CommandTranslationError(
            f"ngdj does not support {operation} of {subject} {change.subject} "
            f"({status.status}){detail}{gap}."
        )
    service = AppBuildStep(
        name_id="ngdj_add_data_service",
        exec_order=4,
        change_op=operation,
        change_reason=(
            f"Required by openapi {change.operation.value}: {change.subject}. "
            f"ngdj {_DATA_SERVICE_COMMAND} creates the service of the new resource "
            f"(on existing output: {mapping.on_existing(_DATA_SERVICE_COMMAND)})."
        ),
        change_target=change.subject,
        change_domain=change.domain,
        ngdj_command=_DATA_SERVICE_COMMAND,
    )
    return (client, service)


def _translate_openui_change(
    change: Change, mapping: CommandMapping | None
) -> tuple[AppBuildStep, ...]:
    """Select the ngdj command that must run for one OpenUI Change.

    The Change records the elements that enclose its path
    (``openui_change_elements``). The command comes from the root node type that
    compiles them, and the upstream mapping says whether it supports the
    operation: anything else fails explicitly, quoting the mapping.
    """
    elements = openui_change_elements(change)
    if not elements:
        raise CommandTranslationError(f"Unsupported Change subject: {change.subject}.")
    if mapping is None:
        raise CommandTranslationError(
            "OpenUI Change translation needs the ngdj command mapping."
        )

    owner = _compiling_element(elements, mapping)
    # A change at the compiled element itself creates or deletes it; a change
    # inside it (an attribute, or an embedded child) updates it.
    at_owner = change.path == owner.path
    operation = change.operation.value if at_owner else ChangeOperation.UPDATE.value
    status = mapping.operation_status(owner.type, operation)
    if status.status != "supported":
        detail = f": {status.reason}" if status.reason else ""
        gap = f" ({status.gap})" if status.gap else ""
        raise CommandTranslationError(
            f"ngdj does not support {operation} of OpenUI node type {owner.type} "
            f"({status.status}){detail}{gap} for {change.subject}."
        )

    element_value = change.before if operation == "delete" else change.after
    command = _select_openui_command(
        mapping, owner.type, element_value if at_owner else None
    )
    tool = _OPENUI_TOOLS.get(command or "")
    if command is None or tool is None:
        compilers = ", ".join(
            entry.command for entry in mapping.commands_for(owner.type)
        )
        raise CommandTranslationError(
            f"No djng Tool runs the ngdj command ({command or compilers}) that "
            f"compiles OpenUI node type {owner.type}: {change.subject}."
        )
    return (
        AppBuildStep(
            name_id=tool.name,
            exec_order=tool.exec_order,
            change_op=operation,
            change_reason=(
                f"Required by openui {change.operation.value}: {change.subject}. "
                f"ngdj {command} compiles {owner.type} {owner.id} "
                f"(on existing output: {mapping.on_existing(command)})."
            ),
            change_target=change.subject,
            change_domain=change.domain,
            node_id=owner.id,
            ngdj_command=command,
        ),
    )


def _compiling_element(
    elements: tuple[OpenUiElement, ...], mapping: CommandMapping
) -> OpenUiElement:
    """The enclosing element whose root node type an ngdj command compiles."""
    nearest = elements[-1]
    if not mapping.has_node_type(nearest.type):
        raise CommandTranslationError(
            f"OpenUI node type {nearest.type} ({nearest.id}) is not covered by "
            "the ngdj command mapping."
        )
    if mapping.role(nearest.type) == "root":
        return nearest
    compilers = mapping.compiled_by(nearest.type)
    for element in reversed(elements[:-1]):
        if element.type in compilers:
            return element
    raise CommandTranslationError(
        f"OpenUI {nearest.type} element {nearest.id} is not inside a node that "
        f"compiles it ({', '.join(compilers)})."
    )


def _select_openui_command(
    mapping: CommandMapping, node_type: str, element: object
) -> str | None:
    """The first command of the node type whose condition holds, if any."""
    for entry in mapping.commands_for(node_type):
        if entry.when is None:
            return entry.command
        condition = _COMMAND_CONDITIONS.get((node_type, entry.command))
        if condition is not None and condition(element):
            return entry.command
    return None


def _change_step(order: int, name: str, change: Change) -> AppBuildStep:
    return AppBuildStep(
        name_id=name,
        exec_order=order,
        change_op=change.operation.value,
        change_reason=(
            f"Required by {change.domain.value} {change.operation.value}: "
            f"{change.subject}."
        ),
        change_target=change.subject,
        change_domain=change.domain,
    )


def _step_sort_key(step: AppBuildStep) -> tuple[int, int, int, str, str]:
    mode_order = {"delete": 0, "update": 1, "move": 1, "create": 2, "validate": 3}
    domain_order = {ChangeDomain.OPENAPI: 0, ChangeDomain.OPENUI: 1}
    return (
        step.exec_order,
        mode_order[step.change_op],
        domain_order.get(step.change_domain, -1),
        step.name_id,
        step.change_target,
    )
