"""Tests for explicit Change-to-command selection and gate ordering."""

from __future__ import annotations

import unittest

from django_angular3.changes import Change, ChangeDomain, ChangeOperation
from django_angular3.command_translation import (
    CommandTranslationError,
    translate_changes,
)


def _change(domain: ChangeDomain, subject: str, operation: ChangeOperation) -> Change:
    return Change(domain, subject, "/subject", operation, None, {"value": True})


class CommandTranslationTests(unittest.TestCase):
    def test_orders_schema_before_openui_and_ends_with_validation(self) -> None:
        commands = translate_changes(
            (
                _change(
                    ChangeDomain.OPENUI,
                    "openui:page:dashboard",
                    ChangeOperation.CREATE,
                ),
                _change(ChangeDomain.OPENAPI, "schema:Pet", ChangeOperation.UPDATE),
            )
        )

        self.assertEqual(commands[-1].name, "terminal-validation")
        self.assertEqual(
            [command.name for command in commands[:-1]],
            [
                "angular-api-integration",
                "angular-data-service-composition",
                "angular-page-composition",
                "angular-page-composition",
            ],
        )
        self.assertEqual(commands[-2].subject, "openui:page:dashboard")

    def test_deletes_precede_creates_at_the_same_dependency_level(self) -> None:
        commands = translate_changes(
            (
                _change(
                    ChangeDomain.OPENUI, "openui:component:old", ChangeOperation.CREATE
                ),
                _change(
                    ChangeDomain.OPENUI, "openui:component:new", ChangeOperation.DELETE
                ),
            )
        )

        self.assertEqual(
            [command.mode for command in commands[:-1]], ["delete", "create"]
        )

    def test_rejects_unmapped_openui_change(self) -> None:
        with self.assertRaisesRegex(
            CommandTranslationError, "Unsupported OpenUI subject"
        ):
            translate_changes(
                (
                    _change(
                        ChangeDomain.OPENUI,
                        "openui:/attrs/title",
                        ChangeOperation.UPDATE,
                    ),
                )
            )

    def test_maps_static_and_project_changes_to_documented_commands(self) -> None:
        commands = translate_changes(
            (
                _change(
                    ChangeDomain.STATIC_CONFIG,
                    "drfSpectacular.settings.TITLE",
                    ChangeOperation.UPDATE,
                ),
                _change(
                    ChangeDomain.STATIC_CONFIG,
                    "angular.workspace.style",
                    ChangeOperation.UPDATE,
                ),
                _change(
                    ChangeDomain.STATIC_CONFIG,
                    "angular.application.ssr",
                    ChangeOperation.UPDATE,
                ),
                _change(
                    ChangeDomain.STATIC_CONFIG,
                    "ngOpenApiGen.serviceSuffix",
                    ChangeOperation.UPDATE,
                ),
                _change(
                    ChangeDomain.PROJECT_CONFIG,
                    "project.name",
                    ChangeOperation.MOVE,
                ),
            )
        )

        self.assertEqual(
            [command.name for command in commands],
            [
                "openapi-schema-export",
                "angular-workspace-foundation",
                "angular-workspace-foundation",
                "angular-app-composition",
                "angular-app-composition",
                "angular-api-integration",
                "terminal-validation",
            ],
        )

    def test_removed_allowlist_entry_rejects_the_selected_command(self) -> None:
        with self.assertRaisesRegex(CommandTranslationError, "no longer authorized"):
            translate_changes(
                (
                    Change(
                        ChangeDomain.STATIC_CONFIG,
                        "tool.commandAllowlist.angular-api-integration",
                        "/tool/commandAllowlist/angular-api-integration",
                        ChangeOperation.DELETE,
                        "angular-api-integration",
                        None,
                    ),
                    _change(ChangeDomain.OPENAPI, "schema:Pet", ChangeOperation.UPDATE),
                )
            )

    def test_openui_move_selects_targeted_page_composition(self) -> None:
        commands = translate_changes(
            (
                _change(
                    ChangeDomain.OPENUI, "openui:page:dashboard", ChangeOperation.MOVE
                ),
            )
        )

        self.assertEqual(commands[0].name, "angular-page-composition")
        self.assertEqual(commands[0].mode, "move")
