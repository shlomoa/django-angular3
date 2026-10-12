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
from django_angular3.config_changes import compare_static_config
from django_angular3.external_comparisons import translate_openui_changelog
from django_angular3.ngdj_command_mapping import CommandMapping
from django_angular3.openapi_changes import translate_oasdiff_detail

STATIC_CONFIG = (
    Path(__file__).resolve().parent.parent / "django_angular3" / "django-angular3.json"
)
SCENARIOS = Path(__file__).resolve().parent / "fixtures" / "scenarios"
FIXTURE_MAPPING = (
    Path(__file__).resolve().parent / "fixtures" / "ngdj" / "command-mapping.json"
)


def _fixture_mapping() -> CommandMapping:
    return CommandMapping(json.loads(FIXTURE_MAPPING.read_text(encoding="utf-8")))


def _change(domain: ChangeDomain, subject: str, operation: ChangeOperation) -> Change:
    return Change(domain, subject, "/subject", operation, None, {"value": True})


class CommandTranslationTests(unittest.TestCase):
    def test_orders_schema_before_openui_and_ends_with_validation(self) -> None:
        commands = translate_changes(
            (
                *_openui_changes([], [{"id": "home", "type": "DashboardPage"}]),
                _change(ChangeDomain.OPENAPI, "path:/pets", ChangeOperation.CREATE),
            ),
            _fixture_mapping(),
        )

        self.assertEqual(commands[-1].name_id, "last-check")
        self.assertEqual(
            [command.name_id for command in commands[:-1]],
            [
                "angular_api_client_generate",
                "ngdj_add_data_service",
                "ngdj_add_page",
            ],
        )
        self.assertEqual(commands[-2].change_target, "openui:/children/home")

    def test_deletes_precede_creates_at_the_same_dependency_level(self) -> None:
        # ngdj supports no OpenUI delete today, so the ordering rule is checked
        # with a mapping that supports deleting a page.
        document = json.loads(FIXTURE_MAPPING.read_text(encoding="utf-8"))
        document["ui"]["nodes"]["DashboardPage"]["operations"]["delete"] = {
            "status": "supported"
        }
        changes = _openui_changes(
            [{"id": "old", "type": "DashboardPage"}],
            [{"id": "new", "type": "DashboardPage"}],
        )

        commands = translate_changes(tuple(reversed(changes)), CommandMapping(document))

        self.assertEqual(
            [(command.change_op, command.exec_order) for command in commands[:-1]],
            [("delete", 10), ("create", 10)],
        )
        self.assertEqual(
            [command.change_target for command in commands[:-1]],
            ["openui:/children/old", "openui:/children/new"],
        )

    def test_an_empty_change_list_gives_no_steps(self) -> None:
        self.assertEqual(translate_changes(()), ())

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
                    ChangeOperation.UPDATE,
                ),
            )
        )

        self.assertEqual(
            [(command.exec_order, command.name_id) for command in commands],
            [
                (0, "openapi_schema_export"),
                (1, "angular-workspace-foundation"),
                (1, "angular-workspace-foundation"),
                (2, "angular-app-composition"),
                (2, "angular-app-composition"),
                (3, "angular_api_client_generate"),
                (12, "last-check"),
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

    def test_first_run_merges_project_steps_into_one_per_command(self) -> None:
        commands = translate_changes(
            tuple(
                _change(ChangeDomain.PROJECT_CONFIG, subject, ChangeOperation.CREATE)
                for subject in PROJECT_CONFIG_CHANGE_TRANSLATORS
            )
        )

        self.assertEqual(
            [command.name_id for command in commands],
            ["angular-workspace-foundation", "angular-app-composition", "last-check"],
        )
        merged = "artifacts.angularWorkspace, project.name"
        for command in commands[:-1]:
            self.assertEqual(command.change_target, merged)
            self.assertIn(merged, command.change_reason)

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

    def test_widgets_and_containers_select_the_tool_of_their_ngdj_command(self) -> None:
        steps = self.translate(
            [],
            [
                {"id": "views", "type": "Tabs"},
                {"id": "confirm", "type": "dialog"},
                {"id": "wizard", "type": "Stepper"},
                {"id": "orders", "type": "table"},
            ],
        )

        self.assertEqual(
            [
                (step.name_id, step.exec_order, step.node_id, step.ngdj_command)
                for step in steps[:-1]
            ],
            [
                ("ngdj_add_dialog", 6, "confirm", "dialog"),
                ("ngdj_add_stepper", 6, "wizard", "stepper"),
                ("ngdj_add_table", 6, "orders", "table"),
                ("ngdj_add_tabs", 6, "views", "tabs"),
            ],
        )

    def test_a_change_inside_a_tabs_container_is_an_unsupported_update(self) -> None:
        with self.assertRaisesRegex(
            CommandTranslationError,
            r"does not support update of OpenUI node type Tabs \(unsupported\)",
        ):
            self.translate(
                [{"id": "views", "type": "Tabs"}],
                [
                    {
                        "id": "views",
                        "type": "Tabs",
                        "attrs": {"uses.orientation": "vertical"},
                    }
                ],
            )

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

    def test_changes_under_one_command_root_become_one_step(self) -> None:
        steps = self.translate(
            [],
            [],
            reference_attrs={"uses.title": '"A"', "uses.theme": '"x"'},
            candidate_attrs={"uses.title": '"B"', "uses.theme": '"y"'},
        )

        (step, _gate) = steps
        self.assertEqual(
            (step.name_id, step.change_op, step.node_id),
            ("angular_app_scaffold", "update", "root"),
        )
        self.assertEqual(
            step.change_target, "openui:/attrs/uses.theme, openui:/attrs/uses.title"
        )
        self.assertIn("openui:/attrs/uses.theme", step.change_reason)
        self.assertIn("openui:/attrs/uses.title", step.change_reason)

    def test_changes_in_several_embedded_nodes_update_their_application_once(
        self,
    ) -> None:
        reference = [
            {
                "id": "routing",
                "type": "Routing",
                "children": [
                    {"id": "r1", "type": "Route", "attrs": {"uses.path": '"a"'}},
                    {"id": "r2", "type": "Route", "attrs": {"uses.path": '"c"'}},
                ],
            }
        ]
        candidate = json.loads(json.dumps(reference))
        candidate[0]["children"][0]["attrs"]["uses.path"] = '"b"'
        candidate[0]["children"][1]["attrs"]["uses.path"] = '"d"'

        (step, _gate) = self.translate(reference, candidate)

        self.assertEqual(
            (step.name_id, step.change_op, step.node_id),
            ("angular_app_scaffold", "update", "root"),
        )
        self.assertEqual(step.change_target.count("openui:/children/routing"), 2)

    def test_changes_under_different_command_roots_stay_separate_steps(self) -> None:
        steps = self.translate(
            [],
            [
                {"id": "home", "type": "DashboardPage"},
                {"id": "about", "type": "DashboardPage"},
            ],
            reference_attrs={"uses.title": '"A"'},
            candidate_attrs={"uses.title": '"B"'},
        )

        self.assertEqual(
            [(step.name_id, step.change_op, step.node_id) for step in steps],
            [
                ("angular_app_scaffold", "update", "root"),
                ("ngdj_add_page", "create", "about"),
                ("ngdj_add_page", "create", "home"),
                ("last-check", "validate", None),
            ],
        )

    def test_a_form_inside_a_created_page_is_compiled_by_the_page(self) -> None:
        steps = self.translate(
            [],
            [
                {
                    "id": "home",
                    "type": "DashboardPage",
                    "children": [
                        {"id": "signup", "type": "Form"},
                        {"id": "card", "type": "SurfaceContainers"},
                    ],
                }
            ],
        )

        self.assertEqual(
            [(step.name_id, step.node_id) for step in steps],
            [("ngdj_add_page", "home"), ("last-check", None)],
        )

    def test_a_form_added_to_an_existing_page_fails_as_a_page_update(self) -> None:
        page = {"id": "home", "type": "DashboardPage"}

        with self.assertRaisesRegex(
            CommandTranslationError,
            r"does not support update of OpenUI node type DashboardPage "
            r"\(unsupported\).*\(shlomoa/angular-django2#\d+\)",
        ):
            self.translate(
                [page], [{**page, "children": [{"id": "f", "type": "Form"}]}]
            )

    def test_the_dashboard_scenario_adds_a_page_to_an_application_with_a_child(
        self,
    ) -> None:
        shared = SCENARIOS / "shared"
        base = json.loads((shared / "base.openui.json").read_text(encoding="utf-8"))
        dashboard = json.loads(
            (shared / "dashboard.openui.json").read_text(encoding="utf-8")
        )
        home = {"id": "home", "type": "EmptyPage"}
        steps = self.translate(
            [home], [home, *dashboard["children"]], reference_attrs=base.get("attrs")
        )

        self.assertEqual(
            [
                (step.name_id, step.exec_order, step.change_op, step.node_id)
                for step in steps
            ],
            [
                ("ngdj_add_page", 10, "create", "dashboardPage"),
                ("last-check", 12, "validate", None),
            ],
        )


class OpenUiMappingCoverageTests(unittest.TestCase):
    """Every operation on every node type of the mapping gives a step or an error.

    The Changes come from the upstream comparison of a document pair built for
    each node type, so the subjects are the real ones. ``move`` is not a row: the
    comparison reports a node moved to another parent as a delete and a create, so
    the delete row covers it.
    """

    mapping: CommandMapping

    @classmethod
    def setUpClass(cls) -> None:
        cls.mapping = _fixture_mapping()

    def _ancestor_types(self, node_type: str) -> list[str]:
        """The compiling parent chain of a node type, outermost first."""
        chain: list[str] = []
        current = node_type
        while True:
            parents = [
                parent
                for parent in self.mapping.compiled_by(current)
                if parent != current and parent != "Application" and parent not in chain
            ]
            if not parents:
                return chain
            chain.insert(0, parents[0])
            current = parents[0]

    def _documents(
        self, node_type: str, operation: str
    ) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
        node: dict[str, object] = {"id": "subject", "type": node_type}
        changed = {**node, "attrs": {"uses.value": '"B"'}}
        original = {**node, "attrs": {"uses.value": '"A"'}}
        before = {"create": None, "update": original, "delete": node}[operation]
        after = {"create": node, "update": changed, "delete": None}[operation]

        chain = self._ancestor_types(node_type)

        def wrap(leaf: dict[str, object] | None) -> list[dict[str, object]]:
            # The ancestors exist on both sides so that only the node differs.
            element = leaf
            for index in reversed(range(len(chain))):
                element = {
                    "id": f"ancestor{index}",
                    "type": chain[index],
                    "children": [] if element is None else [element],
                }
            return [] if element is None else [element]

        return wrap(before), wrap(after)

    def test_every_node_type_and_operation_gives_a_step_or_an_explicit_error(
        self,
    ) -> None:
        outcomes: dict[tuple[str, str], str] = {}
        for node_type in self.mapping.node_types():
            if node_type == "Application":
                continue
            for operation in ("create", "update", "delete"):
                with self.subTest(node_type=node_type, operation=operation):
                    before, after = self._documents(node_type, operation)
                    changes = _openui_changes(before, after)
                    self.assertTrue(changes, "the comparison reported no Change")
                    try:
                        steps = translate_changes(changes, self.mapping)
                    except CommandTranslationError as error:
                        outcomes[(node_type, operation)] = "error"
                        self.assertTrue(str(error))
                    else:
                        outcomes[(node_type, operation)] = "step"
                        self.assertGreater(len(steps), 1, "the Change disappeared")
                        self.assertEqual(steps[-1].name_id, "last-check")

        # The mapping decides: an operation the mapping does not mark supported on
        # the compiling node type never gives a step.
        for (node_type, operation), outcome in outcomes.items():
            if outcome != "step":
                continue
            owner = node_type
            if self.mapping.role(node_type) == "embedded":
                owner = self.mapping.compiled_by(node_type)[0]
                operation = "update"
            self.assertEqual(
                self.mapping.operation_status(owner, operation).status,
                "supported",
                f"{node_type} {operation} gave a step the mapping does not support",
            )

    def test_every_node_type_is_covered_by_a_row(self) -> None:
        self.assertGreater(len(self.mapping.node_types()), 10)
        for node_type in self.mapping.node_types():
            for operation in ("create", "update", "delete", "move"):
                # The mapping answers every cell, so no operation is left undefined.
                self.mapping.operation_status(node_type, operation)

    def test_the_application_attribute_update_is_the_one_root_row(self) -> None:
        (step, _gate) = translate_changes(
            _openui_changes(
                [],
                [],
                reference_attrs={"uses.value": '"A"'},
                candidate_attrs={"uses.value": '"B"'},
            ),
            self.mapping,
        )

        self.assertEqual(
            (step.name_id, step.change_op), ("angular_app_scaffold", "update")
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


class StaticConfigTranslationTests(unittest.TestCase):
    def names(self, subject: str, operation: ChangeOperation) -> list[str]:
        commands = translate_changes(
            (_change(ChangeDomain.STATIC_CONFIG, subject, operation),)
        )
        return [command.name_id for command in commands]

    def test_each_setting_selects_the_command_that_consumes_it(self) -> None:
        cases = {
            "drfSpectacular.settings.TITLE": ("openapi_schema_export", 0),
            "drfSpectacular.settings.SWAGGER_UI_SETTINGS.deepLinking": (
                "openapi_schema_export",
                0,
            ),
            "angular.workspace.style": ("angular-workspace-foundation", 1),
            "angular.workspace.packageManager": ("angular-workspace-foundation", 1),
            "angular.workspace.routing": ("angular-workspace-foundation", 1),
            "tool.ngAddPackage": ("angular-workspace-foundation", 1),
            "angular.application.ssr": ("angular-app-composition", 2),
            "angular.application.zoneless": ("angular-app-composition", 2),
            "ngOpenApiGen.services": ("angular_api_client_generate", 3),
            "ngOpenApiGen.serviceSuffix": ("angular_api_client_generate", 3),
            "ngOpenApiGen.modelIndex": ("angular_api_client_generate", 3),
        }
        for subject, (name, order) in cases.items():
            for operation in (ChangeOperation.CREATE, ChangeOperation.UPDATE):
                with self.subTest(subject=subject, operation=operation.value):
                    commands = translate_changes(
                        (_change(ChangeDomain.STATIC_CONFIG, subject, operation),)
                    )

                    self.assertEqual(
                        [(c.name_id, c.exec_order, c.change_op) for c in commands],
                        [
                            (name, order, operation.value),
                            ("last-check", 12, "validate"),
                        ],
                    )
                    self.assertEqual(commands[0].change_target, subject)
                    self.assertIs(commands[0].change_domain, ChangeDomain.STATIC_CONFIG)

    def test_settings_that_change_no_construction_output_only_add_the_gate(
        self,
    ) -> None:
        for subject in (
            "angular.build.configuration",
            "oasdiff.format",
            "tool.executables.pnpm",
        ):
            with self.subTest(subject=subject):
                self.assertEqual(
                    self.names(subject, ChangeOperation.UPDATE), ["last-check"]
                )

    def test_rejects_unsupported_operations_for_every_setting(self) -> None:
        for subject in (
            "drfSpectacular.settings.TITLE",
            "angular.workspace.style",
            "tool.ngAddPackage",
            "angular.application.ssr",
            "ngOpenApiGen.serviceSuffix",
            "angular.build.configuration",
            "oasdiff.format",
            "tool.executables.ng",
        ):
            for operation in (ChangeOperation.DELETE, ChangeOperation.MOVE):
                with self.subTest(subject=subject, operation=operation.value):
                    with self.assertRaisesRegex(
                        CommandTranslationError, "Unsupported Change operation"
                    ):
                        self.names(subject, operation)

    def test_rejects_a_subject_no_command_consumes(self) -> None:
        for subject in ("angular.unknown.flag", "ngOpenApiGenX.setting", "tool"):
            with self.subTest(subject=subject):
                with self.assertRaisesRegex(
                    CommandTranslationError, "Unsupported Change subject"
                ):
                    self.names(subject, ChangeOperation.UPDATE)

    def test_steps_run_export_workspace_app_then_client(self) -> None:
        subjects = (
            "ngOpenApiGen.serviceSuffix",
            "angular.application.ssr",
            "angular.workspace.style",
            "drfSpectacular.settings.TITLE",
        )

        commands = translate_changes(
            tuple(
                _change(ChangeDomain.STATIC_CONFIG, subject, ChangeOperation.UPDATE)
                for subject in subjects
            )
        )

        self.assertEqual(
            [command.name_id for command in commands],
            [
                "openapi_schema_export",
                "angular-workspace-foundation",
                "angular-app-composition",
                "angular_api_client_generate",
                "last-check",
            ],
        )

    def test_changes_compared_from_the_configuration_translate(self) -> None:
        baseline = json.loads(STATIC_CONFIG.read_text(encoding="utf-8"))
        candidate = json.loads(json.dumps(baseline))
        candidate["angular"]["workspace"]["style"] = "css"
        candidate["ngOpenApiGen"]["serviceSuffix"] = "Client"
        candidate["drfSpectacular"]["settings"]["TITLE"] = "Portal API"

        commands = translate_changes(compare_static_config(baseline, candidate))

        self.assertEqual(
            [command.name_id for command in commands],
            [
                "openapi_schema_export",
                "angular-workspace-foundation",
                "angular_api_client_generate",
                "last-check",
            ],
        )

    def test_every_shipped_setting_is_covered_by_an_initial_build(self) -> None:
        candidate = json.loads(STATIC_CONFIG.read_text(encoding="utf-8"))

        commands = translate_changes(compare_static_config(None, candidate))

        self.assertEqual(commands[-1].name_id, "last-check")
        self.assertEqual(
            {command.name_id for command in commands},
            {
                "openapi_schema_export",
                "angular-workspace-foundation",
                "angular-app-composition",
                "angular_api_client_generate",
                "last-check",
            },
        )
        self.assertTrue(
            all(command.change_op in {"create", "validate"} for command in commands)
        )
