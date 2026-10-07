"""Tests for explicit Change-to-command translation and gate ordering."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from openui_spec import compare

from django_angular3.changes import Change, ChangeDomain, ChangeOperation
from django_angular3.command_translation import (
    PROJECT_CONFIG_CHANGE_TRANSLATORS,
    CommandTranslationError,
    translate_changes,
)
from django_angular3.external_comparisons import translate_openui_changelog
from django_angular3.ngdj_command_mapping import CommandMapping
from django_angular3.openapi_changes import translate_oasdiff_detail

FIXTURE_MAPPING = (
    Path(__file__).resolve().parent / "fixtures" / "ngdj" / "command-mapping.json"
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


def _openui_changes(
    reference_children: list[dict[str, object]],
    candidate_children: list[dict[str, object]],
    *,
    reference_attrs: dict[str, str] | None = None,
    candidate_attrs: dict[str, str] | None = None,
) -> tuple[Change, ...]:
    """Real OpenUI Changes from the upstream comparison of two small documents."""

    def document(children: list[dict[str, object]], attrs: dict[str, str] | None):
        result: dict[str, object] = {
            "version": "0.12.0",
            "id": "root",
            "type": "Application",
            "children": children,
        }
        if attrs is not None:
            result["attrs"] = attrs
        return json.loads(json.dumps(result))

    reference = document(reference_children, reference_attrs)
    candidate = document(candidate_children, candidate_attrs)
    return translate_openui_changelog(
        compare(reference, candidate),
        source="candidate.openui.json",
        reference=reference,
        candidate=candidate,
    )


class OpenUiTranslationTests(unittest.TestCase):
    mapping: CommandMapping

    @classmethod
    def setUpClass(cls) -> None:
        cls.mapping = CommandMapping(
            json.loads(FIXTURE_MAPPING.read_text(encoding="utf-8"))
        )

    def translate(self, *args: object, **kwargs: object):
        return translate_changes(_openui_changes(*args, **kwargs), self.mapping)

    def test_created_nodes_select_their_tool_and_stage(self) -> None:
        steps = self.translate(
            [],
            [
                {"id": "home", "type": "DashboardPage"},
                {"id": "signup", "type": "Form"},
                {"id": "card", "type": "SurfaceContainers"},
                {
                    "id": "dialogCard",
                    "type": "SurfaceContainers",
                    "children": [{"id": "overlay", "type": "OverlayContainers"}],
                },
            ],
        )

        self.assertEqual(
            [(step.name_id, step.exec_order, step.node_id) for step in steps],
            [
                ("ngdj_add_component", 7, "card"),
                ("ngdj_add_complex_component", 8, "dialogCard"),
                ("ngdj_add_reactive_form", 9, "signup"),
                ("ngdj_add_page", 10, "home"),
                ("last-check", 12, None),
            ],
        )
        for step in steps[:-1]:
            self.assertEqual(step.change_op, "create")
            self.assertIs(step.change_domain, ChangeDomain.OPENUI)

    def test_a_step_reason_names_the_command_and_its_existing_output_behavior(
        self,
    ) -> None:
        (step, _gate) = self.translate([], [{"id": "home", "type": "DashboardPage"}])

        self.assertEqual(step.change_target, "openui:/children/home")
        self.assertIn("ngdj page compiles DashboardPage home", step.change_reason)
        self.assertIn("refuse-modified", step.change_reason)

    def test_an_application_attribute_update_runs_the_app_scaffold(self) -> None:
        (step, _gate) = self.translate(
            [],
            [],
            reference_attrs={"uses.title": '"A"'},
            candidate_attrs={"uses.title": '"B"'},
        )

        self.assertEqual(
            (step.name_id, step.exec_order, step.change_op, step.node_id),
            ("angular_app_scaffold", 2, "update", "root"),
        )

    def test_a_change_in_an_embedded_node_updates_the_application_that_compiles_it(
        self,
    ) -> None:
        reference = [
            {
                "id": "routing",
                "type": "Routing",
                "children": [
                    {"id": "r1", "type": "Route", "attrs": {"uses.path": '"a"'}}
                ],
            }
        ]
        candidate = json.loads(json.dumps(reference))
        candidate[0]["children"][0]["attrs"]["uses.path"] = '"b"'

        (step, _gate) = self.translate(reference, candidate)

        self.assertEqual(
            (step.name_id, step.change_op, step.node_id),
            ("angular_app_scaffold", "update", "root"),
        )

    def test_an_unsupported_operation_quotes_the_mapping_reason_and_gap(self) -> None:
        reference = [
            {"id": "home", "type": "DashboardPage", "attrs": {"uses.title": '"A"'}}
        ]
        candidate = json.loads(json.dumps(reference))
        candidate[0]["attrs"]["uses.title"] = '"B"'

        with self.assertRaisesRegex(
            CommandTranslationError,
            r"does not support update of OpenUI node type DashboardPage "
            r"\(unsupported\): .*\(shlomoa/angular-django2#\d+\)",
        ):
            self.translate(reference, candidate)

    def test_deleting_a_node_fails_explicitly(self) -> None:
        with self.assertRaisesRegex(
            CommandTranslationError, r"does not support delete of OpenUI node type Form"
        ):
            self.translate([{"id": "signup", "type": "Form"}], [])

    def test_a_node_whose_command_has_no_djng_tool_fails_as_no_tool(self) -> None:
        with self.assertRaisesRegex(
            CommandTranslationError, r"No djng Tool runs the ngdj command \(tabs\)"
        ):
            self.translate([], [{"id": "views", "type": "Tabs"}])

    def test_commands_chosen_by_an_unevaluated_condition_have_no_djng_tool(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            CommandTranslationError,
            r"No djng Tool runs the ngdj command \(form-field, field-component\)",
        ):
            self.translate([], [{"id": "email", "type": "TextInputs"}])

    def test_a_node_type_missing_from_the_mapping_is_not_guessed(self) -> None:
        with self.assertRaisesRegex(
            CommandTranslationError,
            "Grid .* is not covered by the ngdj command mapping",
        ):
            self.translate([], [{"id": "layout", "type": "Grid"}])

    def test_openui_changes_need_the_command_mapping(self) -> None:
        changes = _openui_changes([], [{"id": "home", "type": "DashboardPage"}])

        with self.assertRaisesRegex(
            CommandTranslationError, "needs the ngdj command mapping"
        ):
            translate_changes(changes)

    def test_openui_steps_sort_with_the_other_domains(self) -> None:
        openui = _openui_changes([], [{"id": "home", "type": "DashboardPage"}])
        project = _change(
            ChangeDomain.PROJECT_CONFIG, "project.name", ChangeOperation.UPDATE
        )

        steps = translate_changes((*openui, project), self.mapping)

        self.assertEqual(
            [step.name_id for step in steps],
            [
                "angular-workspace-foundation",
                "angular-app-composition",
                "ngdj_add_page",
                "last-check",
            ],
        )


class OpenApiTranslationTests(unittest.TestCase):
    mapping: CommandMapping

    @classmethod
    def setUpClass(cls) -> None:
        cls.mapping = CommandMapping(
            json.loads(FIXTURE_MAPPING.read_text(encoding="utf-8"))
        )

    def translate(self, subject: str, operation: ChangeOperation):
        return translate_changes(
            (_change(ChangeDomain.OPENAPI, subject, operation),), self.mapping
        )

    def test_a_new_path_regenerates_the_client_and_creates_its_data_service(
        self,
    ) -> None:
        steps = self.translate("path:/pets", ChangeOperation.CREATE)

        self.assertEqual(
            [(step.name_id, step.exec_order, step.change_op) for step in steps],
            [
                ("angular_api_client_generate", 3, "create"),
                ("ngdj_add_data_service", 4, "create"),
                ("last-check", 12, "validate"),
            ],
        )
        for step in steps[:-1]:
            self.assertEqual(step.change_target, "path:/pets")
            self.assertIs(step.change_domain, ChangeDomain.OPENAPI)
        self.assertIn("on existing output: skip", steps[1].change_reason)

    def test_a_new_schema_only_regenerates_the_client(self) -> None:
        steps = self.translate("schema:Pet", ChangeOperation.CREATE)

        self.assertEqual(
            [step.name_id for step in steps],
            ["angular_api_client_generate", "last-check"],
        )

    def test_changes_that_would_update_or_delete_data_services_fail_explicitly(
        self,
    ) -> None:
        cases = (
            (
                "operation:GET /pets",
                ChangeOperation.CREATE,
                "update of the data service",
            ),
            (
                "operation:GET /pets",
                ChangeOperation.UPDATE,
                "update of the data service",
            ),
            (
                "operation:GET /pets",
                ChangeOperation.DELETE,
                "update of the data service",
            ),
            ("path:/pets", ChangeOperation.DELETE, "delete of the data service"),
            ("schema:Pet", ChangeOperation.UPDATE, "update of the data services that"),
            ("schema:Pet", ChangeOperation.DELETE, "delete of the data services that"),
        )
        for subject, operation, expected in cases:
            with self.subTest(subject=subject, operation=operation.value):
                with self.assertRaisesRegex(
                    CommandTranslationError,
                    rf"ngdj does not support {expected}.* {subject} \(unsupported\): "
                    r".*\(shlomoa/angular-django2#\d+\)",
                ):
                    self.translate(subject, operation)

    def test_an_unknown_subject_kind_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            CommandTranslationError, "Unsupported Change subject: server:prod"
        ):
            self.translate("server:prod", ChangeOperation.CREATE)

    def test_openapi_changes_need_the_command_mapping(self) -> None:
        change = _change(ChangeDomain.OPENAPI, "path:/pets", ChangeOperation.CREATE)

        with self.assertRaisesRegex(
            CommandTranslationError, "needs the ngdj command mapping"
        ):
            translate_changes((change,))

    def test_api_steps_precede_the_openui_steps_they_support(self) -> None:
        openui = _openui_changes([], [{"id": "home", "type": "DashboardPage"}])
        api = _change(ChangeDomain.OPENAPI, "path:/pets", ChangeOperation.CREATE)

        steps = translate_changes((*openui, api), self.mapping)

        self.assertEqual(
            [step.name_id for step in steps],
            [
                "angular_api_client_generate",
                "ngdj_add_data_service",
                "ngdj_add_page",
                "last-check",
            ],
        )

    def test_changes_derived_from_an_oasdiff_detail_translate(self) -> None:
        candidate = {
            "paths": {"/pets": {"get": {}}},
            "components": {"schemas": {"Pet": {"type": "object"}}},
        }
        changes = translate_oasdiff_detail(
            {
                "paths": {"added": ["/pets"]},
                "components": {"schemas": {"added": ["Pet"]}},
            },
            {"paths": {}, "components": {"schemas": {}}},
            candidate,
            source="candidate.openapi.json",
        )

        steps = translate_changes(changes, self.mapping)

        self.assertEqual(
            [(step.name_id, step.change_target) for step in steps],
            [
                ("angular_api_client_generate", "path:/pets"),
                ("angular_api_client_generate", "schema:Pet"),
                ("ngdj_add_data_service", "path:/pets"),
                ("last-check", "changeset"),
            ],
        )
