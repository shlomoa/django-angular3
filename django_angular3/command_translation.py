"""Deterministically translate Changes into an ordered plan of AppBuildSteps."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Final

from .changes import Change, ChangeDomain


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
    page name or path). Identical steps from different Changes are not merged.

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
            ``openui:page:home`` or ``path:/api/items``), or ``changeset``
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
    steps = [step for change in changes for step in _change_steps(change)]
    if not steps:
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


ChangeTranslator = Callable[[Change], tuple[AppBuildStep, ...]]


def _not_implemented(change: Change) -> tuple[AppBuildStep, ...]:
    """Placeholder for a mapped name whose translation is not implemented yet."""
    raise CommandTranslationError(
        f"Translation not implemented for {change.domain.value} "
        f"{change.operation.value}: {change.subject}."
    )


# Per-domain maps
# ordered steps for that Change. The longest matching prefix wins.
OPENAPI_CHANGE_TRANSLATORS: Final[dict[str, ChangeTranslator]] = {
    # TODO: populate OpenAPI subject-prefix translators.
}
PROJECT_CONFIG_CHANGE_TRANSLATORS: Final[dict[str, ChangeTranslator]] = {
    # TODO: populate project-config subject-prefix translators.
}
STATIC_CONFIG_CHANGE_TRANSLATORS: Final[dict[str, ChangeTranslator]] = {
    # TODO: populate static-config subject-prefix translators.
}
OPENUI_CHANGE_TRANSLATORS: Final[dict[str, ChangeTranslator]] = {
    # TODO: populate OpenUI subject-prefix translators.
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
