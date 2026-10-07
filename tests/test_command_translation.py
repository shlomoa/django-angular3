"""Tests for explicit Change-to-command translation and gate ordering."""

from __future__ import annotations

import unittest

from django_angular3.changes import Change, ChangeDomain, ChangeOperation
from django_angular3.command_translation import (
    PROJECT_CONFIG_CHANGE_TRANSLATORS,
    CommandTranslationError,
    translate_changes,
)


def _change(domain: ChangeDomain, subject: str, operation: ChangeOperation) -> Change:
    return Change(domain, subject, "/subject", operation, None, {"value": True})


class CommandTranslationTests(unittest.TestCase):
    # https://github.com/shlomoa/django-angular3/issues/204:
    # Remove each expectedFailure when its mapping and ordering assertions pass.
    @unittest.expectedFailure
    def test_orders_schema_before_openui_and_ends_with_validation(self) -> None:
        commands = translate_changes(
            (
                _change(
                    ChangeDomain.OPENUI,
                    "openui:/children/dashboard",
                    ChangeOperation.CREATE,
                ),
                _change(ChangeDomain.OPENAPI, "schema:Pet", ChangeOperation.UPDATE),
            )
        )

        self.assertEqual(commands[-1].name_id, "last-check")
        self.assertEqual(
            [command.name_id for command in commands[:-1]],
            [
                "angular-api-integration",
                "angular-data-service-composition",
                "angular-page-composition",
                "angular-page-composition",
            ],
        )
        self.assertEqual(commands[-2].change_target, "openui:/children/dashboard")

    @unittest.expectedFailure
    def test_deletes_precede_creates_at_the_same_dependency_level(self) -> None:
        commands = translate_changes(
            (
                _change(
                    ChangeDomain.OPENUI, "openui:/children/old", ChangeOperation.CREATE
                ),
                _change(
                    ChangeDomain.OPENUI, "openui:/children/new", ChangeOperation.DELETE
                ),
            )
        )

        self.assertEqual(
            [command.change_op for command in commands[:-1]], ["delete", "create"]
        )

    def test_rejects_unmapped_openui_change(self) -> None:
        with self.assertRaisesRegex(
            CommandTranslationError, "Unsupported Change subject"
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

    @unittest.expectedFailure
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
            [command.name_id for command in commands],
            [
                "openapi-schema-export",
                "angular-workspace-foundation",
                "angular-workspace-foundation",
                "angular-app-composition",
                "angular-app-composition",
                "angular-api-integration",
                "last-check",
            ],
        )

    def test_rejects_openui_move_explicitly(self) -> None:
        # `move` is reserved: the OpenUI comparison emits no `move`, and no
        # translation exists for it, so it must fail rather than be omitted.
        with self.assertRaisesRegex(CommandTranslationError, "Unsupported Change"):
            translate_changes(
                (
                    _change(
                        ChangeDomain.OPENUI,
                        "openui:/children/dashboard",
                        ChangeOperation.MOVE,
                    ),
                )
            )


class ProjectConfigTranslationTests(unittest.TestCase):
    def test_project_identity_and_workspace_need_foundation_commands(self) -> None:
        for subject in ("project.name", "artifacts.angularWorkspace"):
            for operation in (ChangeOperation.CREATE, ChangeOperation.UPDATE):
                with self.subTest(subject=subject, operation=operation):
                    commands = translate_changes(
                        (_change(ChangeDomain.PROJECT_CONFIG, subject, operation),)
                    )

                    self.assertEqual(
                        [command.name_id for command in commands],
                        [
                            "angular-workspace-foundation",
                            "angular-app-composition",
                            "last-check",
                        ],
                    )
                    self.assertEqual(
                        [command.exec_order for command in commands], [1, 2, 12]
                    )
                    for command in commands[:-1]:
                        self.assertEqual(command.change_op, operation.value)
                        self.assertEqual(command.change_target, subject)
                        self.assertIs(
                            command.change_domain, ChangeDomain.PROJECT_CONFIG
                        )

    def test_source_selectors_only_add_the_validation_gate(self) -> None:
        for subject in ("artifacts.openapiSchema", "artifacts.openuiSpecification"):
            for operation in (ChangeOperation.CREATE, ChangeOperation.UPDATE):
                with self.subTest(subject=subject, operation=operation):
                    commands = translate_changes(
                        (_change(ChangeDomain.PROJECT_CONFIG, subject, operation),)
                    )

                    self.assertEqual(
                        [command.name_id for command in commands], ["last-check"]
                    )

    def test_selector_change_leaves_other_domain_steps_untouched(self) -> None:
        commands = translate_changes(
            (
                _change(
                    ChangeDomain.PROJECT_CONFIG,
                    "artifacts.openuiSpecification",
                    ChangeOperation.UPDATE,
                ),
                _change(
                    ChangeDomain.PROJECT_CONFIG,
                    "project.name",
                    ChangeOperation.CREATE,
                ),
            )
        )

        self.assertEqual(
            [command.name_id for command in commands],
            ["angular-workspace-foundation", "angular-app-composition", "last-check"],
        )

    def test_rejects_unsupported_operations_for_every_subject(self) -> None:
        for subject in PROJECT_CONFIG_CHANGE_TRANSLATORS:
            for operation in (ChangeOperation.DELETE, ChangeOperation.MOVE):
                with self.subTest(subject=subject, operation=operation):
                    with self.assertRaisesRegex(
                        CommandTranslationError, "Unsupported Change operation"
                    ):
                        translate_changes(
                            (_change(ChangeDomain.PROJECT_CONFIG, subject, operation),)
                        )

    def test_rejects_unmapped_project_subject(self) -> None:
        with self.assertRaisesRegex(
            CommandTranslationError, "Unsupported Change subject"
        ):
            translate_changes(
                (
                    _change(
                        ChangeDomain.PROJECT_CONFIG,
                        "artifacts.unknown",
                        ChangeOperation.CREATE,
                    ),
                )
            )

    def test_registers_exactly_the_compared_project_config_subjects(self) -> None:
        self.assertEqual(
            set(PROJECT_CONFIG_CHANGE_TRANSLATORS),
            {
                "project.name",
                "artifacts.openapiSchema",
                "artifacts.openuiSpecification",
                "artifacts.angularWorkspace",
            },
        )
