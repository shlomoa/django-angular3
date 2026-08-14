"""Deterministically select documented construction commands from Changes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from .changes import Change, ChangeDomain, ChangeOperation


class CommandTranslationError(ValueError):
    """Raised when no documented command mapping exists for a Change."""


@dataclass(frozen=True)
class CommandSelection:
    """One ordered command or validation gate selected from an atomic Change."""

    name: str
    order: int
    mode: str
    reason: str
    subject: str
    domain: ChangeDomain | None


_OPENAPI_COMMANDS: Final = (
    (3, "angular-api-integration"),
    (4, "angular-data-service-composition"),
    (10, "angular-page-composition"),
)
_OPENUI_PREFIXES: Final = {
    "openui:page:": (10, "angular-page-composition"),
    "openui:component:": (7, "angular-component-composition"),
    "openui:complex-component:": (8, "angular-complex-component-composition"),
    "openui:reactive-form:": (9, "angular-reactive-form-composition"),
    "openui:navigation:": (11, "angular-site-composition"),
}


def translate_changes(changes: tuple[Change, ...]) -> tuple[CommandSelection, ...]:
    """Translate supported changes into ordered commands and a terminal gate.

    This is selection only: it neither invokes wrappers nor changes the
    generated-app workspace. Every unsupported semantic subject is rejected.
    """
    selections = [selection for change in changes for selection in _select(change)]
    _reject_removed_selected_commands(changes, selections)
    if not selections:
        return ()
    selections.append(
        CommandSelection(
            name="terminal-validation",
            order=12,
            mode="validate",
            reason="Validate all selected construction outputs.",
            subject="changeset",
            domain=None,
        )
    )
    return tuple(sorted(selections, key=_selection_key))


def _select(change: Change) -> tuple[CommandSelection, ...]:
    if change.domain is ChangeDomain.OPENAPI:
        if not change.subject.startswith(("path:", "operation:", "schema:")):
            raise CommandTranslationError(
                f"Unsupported OpenAPI subject: {change.subject}."
            )
        return tuple(
            _selection(order, name, change) for order, name in _OPENAPI_COMMANDS
        )
    if change.domain is ChangeDomain.PROJECT_CONFIG:
        if change.operation not in {
            ChangeOperation.UPDATE,
            ChangeOperation.MOVE,
            ChangeOperation.CREATE,
        }:
            raise CommandTranslationError(
                f"Unsupported project configuration change: {change.path}."
            )
        return tuple(
            _selection(order, name, change)
            for order, name in (
                (1, "angular-workspace-foundation"),
                (2, "angular-app-composition"),
            )
        )
    if change.domain is ChangeDomain.STATIC_CONFIG:
        return _static_config_selection(change)
    if change.domain is ChangeDomain.OPENUI:
        for prefix, (order, name) in _OPENUI_PREFIXES.items():
            if change.subject.startswith(prefix):
                if prefix == "openui:navigation:" and change.operation not in {
                    ChangeOperation.UPDATE,
                    ChangeOperation.MOVE,
                }:
                    raise CommandTranslationError(
                        f"Unsupported OpenUI navigation operation: {change.operation}."
                    )
                return (_selection(order, name, change),)
        raise CommandTranslationError(f"Unsupported OpenUI subject: {change.subject}.")
    raise CommandTranslationError(f"Unsupported Change domain: {change.domain}.")


def _selection(order: int, name: str, change: Change) -> CommandSelection:
    return CommandSelection(
        name=name,
        order=order,
        mode=change.operation.value,
        reason=(
            f"Selected for {change.domain.value} {change.operation.value}: "
            f"{change.subject}."
        ),
        subject=change.subject,
        domain=change.domain,
    )


def _static_config_selection(change: Change) -> tuple[CommandSelection, ...]:
    if change.subject.startswith("tool.commandAllowlist."):
        if change.operation not in {ChangeOperation.CREATE, ChangeOperation.DELETE}:
            raise CommandTranslationError(
                f"Unsupported command allowlist change: {change.path}."
            )
        return ()
    if change.subject.startswith("ngOpenApiGen."):
        return (_selection(3, "angular-api-integration", change),)
    if change.subject.startswith("drfSpectacular.settings."):
        return (_selection(0, "openapi-schema-export", change),)
    if change.subject.startswith(
        ("angular.workspace.", "tool.executables.", "tool.ngAddPackage")
    ):
        return (_selection(1, "angular-workspace-foundation", change),)
    if change.subject.startswith(("angular.application.", "angular.build.")):
        return (_selection(2, "angular-app-composition", change),)
    raise CommandTranslationError(
        f"Unsupported static configuration change: {change.path}."
    )


def _reject_removed_selected_commands(
    changes: tuple[Change, ...], selections: list[CommandSelection]
) -> None:
    removed = {
        str(change.before)
        for change in changes
        if change.domain is ChangeDomain.STATIC_CONFIG
        and change.subject.startswith("tool.commandAllowlist.")
        and change.operation is ChangeOperation.DELETE
    }
    selected = {selection.name for selection in selections}
    unauthorized = sorted(removed & selected)
    if unauthorized:
        raise CommandTranslationError(
            "Selected command(s) are no longer authorized: "
            + ", ".join(unauthorized)
            + "."
        )


def _selection_key(selection: CommandSelection) -> tuple[int, int, int, str, str]:
    mode_order = {"delete": 0, "update": 1, "move": 1, "create": 2, "validate": 3}
    domain_order = {ChangeDomain.OPENAPI: 0, ChangeDomain.OPENUI: 1}
    return (
        selection.order,
        mode_order[selection.mode],
        domain_order.get(selection.domain, -1),
        selection.name,
        selection.subject,
    )
