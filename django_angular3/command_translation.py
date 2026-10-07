"""Deterministically translate Changes into an ordered plan of AppBuildSteps."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Final

from .changes import Change, ChangeDomain, ChangeOperation


class CommandTranslationError(ValueError):
    """Raised when no documented command mapping exists for a Change."""


@dataclass(frozen=True)
class AppBuildStep:
    """One ordered step of the app build plan: a construction command or gate.

    A step is produced from one atomic Change (a single Change can yield
    several steps, for example an OpenAPI change yields three), except for the
    final ``last-check`` gate, which is appended once for the whole
    change set. A step only describes what should run; it does not execute
    anything, and it does not carry the options a command needs (such as a
    page name or path). Identical steps from different Changes are not merged, except
    that project-config steps are merged into one step that lists every subject
    (see ``_merge_project_steps``).

    Steps are sorted by ``exec_order``, then ``change_op``, ``change_domain``,
    ``name_id`` and ``change_target`` (see ``_step_sort_key``) to keep plans
    deterministic.

    Attributes:
        name_id: Skill-layer identifier of the construction command (for
            example ``angular-page-composition``), or ``last-check`` for the
            final gate.
            ``ng_page``; see ``doc/ARCHITECTURE.md`` §3.6.4 for the naming
            layers.
        exec_order: Pipeline stage number.
            1 workspace foundation, 2 app composition, 3 API integration,
            4 data services, 7 components, 8 complex components, 9 reactive
            forms, 10 pages, 11 site navigation, 12 last validation.
            Values 5 and 6 are currently unused.
        change_op: What the command should do. One of the ``ChangeOperation``
            values (``create``, ``update``, ``move``, ``delete``) copied from
            the originating Change, or ``validate`` for the last gate.
            Breaks ties between steps with the same ``exec_order``:
            then update and move, then create, then validate.
        change_reason: Human-readable explanation of which Change required
            the step, for plan output and debug logs.
        change_target: Identifier of the thing the Change affects (for example
            ``openui:/children/home`` or ``path:/api/items``), or ``changeset``
            for the last gate.
        change_domain: ``ChangeDomain`` the originating Change belongs to, or
            ``None`` for the last gate, which covers the whole change set.
            Breaks ties after ``change_op``:
            OpenUI, with all other domains and ``None`` sorting before both.
    """

    name_id: str
    exec_order: int
    change_op: str
    change_reason: str
    change_target: str
    change_domain: ChangeDomain | None


def translate_changes(changes: tuple[Change, ...]) -> tuple[AppBuildStep, ...]:
    """Translate supported changes into ordered commands and a last gate.

    This only plans: it neither invokes wrappers nor changes the
    generated-app workspace. Every unsupported semantic subject is rejected.
    """
    steps = _merge_project_steps(
        [step for change in changes for step in _change_steps(change)]
    )
    if not changes:
        raise CommandTranslationError()
    steps.append(
        AppBuildStep(
            name_id="last-check",
            exec_order=12,
            change_op="validate",
            change_reason="Validate the outputs of all steps in the plan.",
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


_PROJECT_CONFIG_OPERATIONS: Final = (ChangeOperation.CREATE, ChangeOperation.UPDATE)


def _require_project_config_operation(change: Change) -> None:
    """Reject operations without a documented project-config translation.

    The project-config comparison emits only ``create`` (no baseline) and
    ``update``. ``delete`` and ``move`` have no translation, so they fail
    explicitly instead of being planned as no work.
    """
    if change.operation not in _PROJECT_CONFIG_OPERATIONS:
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
    _require_project_config_operation(change)
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
    _require_project_config_operation(change)
    return ()


# Per-domain maps from a Change subject to the translator that returns the
# ordered steps for that Change. The subject must match a key exactly.
OPENAPI_CHANGE_TRANSLATORS: Final[dict[str, ChangeTranslator]] = {
    # TODO: populate OpenAPI subject translators.
}
PROJECT_CONFIG_CHANGE_TRANSLATORS: Final[dict[str, ChangeTranslator]] = {
    "project.name": _translate_project_foundation,
    "artifacts.angularWorkspace": _translate_project_foundation,
    "artifacts.openapiSchema": _translate_project_selector,
    "artifacts.openuiSpecification": _translate_project_selector,
}
STATIC_CONFIG_CHANGE_TRANSLATORS: Final[dict[str, ChangeTranslator]] = {
    # TODO: populate static-config subject translators.
}
OPENUI_CHANGE_TRANSLATORS: Final[dict[str, ChangeTranslator]] = {
    # TODO: populate OpenUI subject translators.
}


DOMAIN_CHANGE_TRANSLATORS: Final[dict[ChangeDomain, dict[str, ChangeTranslator]]] = {
    ChangeDomain.OPENAPI: OPENAPI_CHANGE_TRANSLATORS,
    ChangeDomain.PROJECT_CONFIG: PROJECT_CONFIG_CHANGE_TRANSLATORS,
    ChangeDomain.STATIC_CONFIG: STATIC_CONFIG_CHANGE_TRANSLATORS,
    ChangeDomain.OPENUI: OPENUI_CHANGE_TRANSLATORS,
}


def _change_steps(change: Change) -> tuple[AppBuildStep, ...]:
    translators = DOMAIN_CHANGE_TRANSLATORS.get(change.domain)
    if translators is None:
        raise CommandTranslationError(f"Unsupported Change domain: {change.domain}.")
    if change.subject not in translators:
        raise CommandTranslationError(f"Unsupported Change subject: {change.subject}.")
    return translators[change.subject](change)


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
