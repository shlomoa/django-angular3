"""``build_app`` dry-run coverage of the scenario suite.

The oracles are the ordered steps the translators emit for each scenario
(``TEST_SCENARIO_SPECIFICATIONS.md`` §3). Every scenario is exercised as an initial
build (no previous configuration), and the scenarios whose previous state is a
fixture pair are also compared incrementally. A scenario whose oracle needs an
update or delete the ngdj mapping does not support asserts the explicit failure.
Incremental OpenAPI comparison needs a real ``oasdiff`` and is skipped without one.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import django

from django_angular3.changes import ChangeDomain
from django_angular3.command_translation import (
    CommandTranslationError,
    translate_changes,
)
from django_angular3.config_changes import compare_static_config
from django_angular3.consistency import reference_index
from django_angular3.management.commands.build_app import (
    ChangeDetector,
    Configuration,
)
from django_angular3.ngdj_command_mapping import CommandMapping
from tests.test_command_translation import FIXTURE_MAPPING
from tests.tool_config import use_tool_configuration_template
from tests.workspace_temp import WORKSPACE_TEMP_DIR

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.test_settings")
django.setup()

SCENARIOS = Path(__file__).resolve().parent / "fixtures" / "scenarios"
SHARED = SCENARIOS / "shared"
INITIAL_FOUNDATION = [
    (1, "angular-workspace-foundation", "create"),
    (2, "ngdj_run_schematic", "create"),
    (2, "angular_app_scaffold", "create"),
    (3, "angular_api_client_generate", "create"),
]
CHECK = (12, "last-check", "validate")
SERVICE = (4, "ngdj_add_data_service", "create")
PAGE = (10, "ngdj_add_page", "create")

# scenario id -> the steps of its initial build (no previous configuration).
INITIAL_BUILD: dict[str, list[tuple[int, str, str]]] = {
    "02-add-order": [*INITIAL_FOUNDATION, SERVICE, SERVICE, CHECK],
    "03-schema-removal": [*INITIAL_FOUNDATION, SERVICE, CHECK],
    "04-workspace-style": [*INITIAL_FOUNDATION, SERVICE, CHECK],
    "05-openui-source": [*INITIAL_FOUNDATION, SERVICE, CHECK],
    "06-add-dashboard": [*INITIAL_FOUNDATION, SERVICE, PAGE, CHECK],
    "07-combined-change": [*INITIAL_FOUNDATION, SERVICE, SERVICE, PAGE, CHECK],
    "08-replace-resource": [*INITIAL_FOUNDATION, SERVICE, CHECK],
    "09-no-change": [*INITIAL_FOUNDATION, SERVICE, CHECK],
    "10-config-openapi": [*INITIAL_FOUNDATION, SERVICE, SERVICE, CHECK],
    "11-config-openui": [*INITIAL_FOUNDATION, SERVICE, PAGE, CHECK],
    "12-all-change-domains": [*INITIAL_FOUNDATION, SERVICE, SERVICE, PAGE, CHECK],
}


def setUpModule() -> None:
    use_tool_configuration_template()


def _oasdiff_available() -> bool:
    """Whether an oasdiff executable is on PATH; never downloads one."""
    return shutil.which("oasdiff") is not None


def _current_config(scenario: str) -> Path:
    return next(
        path
        for path in sorted((SCENARIOS / scenario).glob("*.json"))
        if ".previous" not in path.name
    )


def _project_name(scenario: str) -> str:
    document = json.loads(_current_config(scenario).read_text(encoding="utf-8"))
    return document["project"]["name"]


def _step_keys(steps) -> list[tuple[int, str, str]]:
    return [(step.exec_order, step.name_id, step.change_op) for step in steps]


class ScenarioDryRunTests(unittest.TestCase):
    mapping: CommandMapping

    @classmethod
    def setUpClass(cls) -> None:
        cls.mapping = CommandMapping(
            json.loads(FIXTURE_MAPPING.read_text(encoding="utf-8"))
        )

    def _translate(self, current: Path, previous: Configuration | None):
        change_set = ChangeDetector(Configuration(current), previous).detect_changes()
        changes = tuple(
            change
            for domain in ChangeDomain
            for change in change_set.domains[domain].changes
        )
        return change_set, translate_changes(changes, self.mapping)

    def test_the_scenario_matrix_and_the_oracles_cover_the_same_scenarios(self) -> None:
        matrix = json.loads((SCENARIOS / "scenario-matrix.json").read_text("utf-8"))

        self.assertEqual(
            {entry["id"] for entry in matrix},
            set(INITIAL_BUILD),
        )

    def test_every_scenario_is_an_initial_build_without_a_previous_configuration(
        self,
    ) -> None:
        for scenario, expected in INITIAL_BUILD.items():
            with self.subTest(scenario=scenario):
                _, steps = self._translate(_current_config(scenario), None)

                self.assertEqual(_step_keys(steps), expected)

    def test_a_concern_backed_by_both_sources_keeps_each_source_identity(self) -> None:
        # The OpenUI bindings name OpenAPI operations: one concern is both
        # API-contract-backed and UI-description-derived. The derivation must keep the
        # two sources apart: each Change stays in its domain with the evidence of its
        # own file, and each step names the one domain that caused it.
        directory = tempfile.TemporaryDirectory(dir=WORKSPACE_TEMP_DIR)
        self.addCleanup(directory.cleanup)
        openapi = SHARED / "bindings.openapi.json"
        document = json.loads((SHARED / "invoice.openui.json").read_text("utf-8"))
        document["children"][0]["attrs"] = {
            "uses.data": "src/app/api/services#UsersApiService"
        }
        openui = Path(directory.name) / "bound.openui.json"
        openui.write_text(json.dumps(document), encoding="utf-8")
        config = Path(directory.name) / "django-angular3-bound.json"
        config.write_text(
            json.dumps(
                {
                    "project": {"name": "bound"},
                    "artifacts": {
                        "openapiSchema": str(openapi),
                        "openuiSpecification": str(openui),
                        "angularWorkspace": str(Path(directory.name) / "angular"),
                    },
                }
            ),
            encoding="utf-8",
        )
        index = reference_index(
            json.loads(openui.read_text("utf-8")),
            json.loads(openapi.read_text("utf-8")),
        )
        self.assertTrue(index.operations, "the OpenUI document binds API operations")

        change_set, steps = self._translate(config, None)

        api = change_set.domains[ChangeDomain.OPENAPI].changes
        ui = change_set.domains[ChangeDomain.OPENUI].changes
        self.assertTrue(api and ui)
        self.assertFalse({c.subject for c in api} & {c.subject for c in ui})
        for change in api:
            self.assertEqual(change.domain, ChangeDomain.OPENAPI)
            self.assertFalse(change.subject.startswith("openui:"))
            self.assertEqual(
                {e.source for e in change.evidence}, {str(openapi)}, change.subject
            )
        for change in ui:
            self.assertEqual(change.domain, ChangeDomain.OPENUI)
            self.assertTrue(change.subject.startswith("openui:"))
            self.assertEqual(
                {e.source for e in change.evidence}, {str(openui)}, change.subject
            )
        by_domain = {
            ChangeDomain.OPENAPI: {c.subject for c in api},
            ChangeDomain.OPENUI: {c.subject for c in ui},
        }
        for step in steps:
            if step.change_domain in by_domain:
                targets = {t.strip() for t in step.change_target.split(",")}
                self.assertTrue(
                    targets
                    <= by_domain[step.change_domain]
                    | {"artifacts.angularWorkspace", "project.name"},
                    (step.name_id, step.change_target),
                )
        self.assertIn(
            ChangeDomain.OPENAPI,
            {s.change_domain for s in steps if s.name_id == "ngdj_add_data_service"},
        )
        self.assertTrue(
            {s.change_domain for s in steps if s.name_id == "ngdj_add_page"}
            <= {ChangeDomain.OPENUI}
        )

    def test_the_initial_build_of_an_uncompilable_document_fails_explicitly(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            CommandTranslationError, "DataGrid.*not covered by the ngdj command mapping"
        ):
            self._translate(_current_config("13-dangling-binding"), None)

    def _previous(self, scenario: str, openapi: str, openui: str) -> Configuration:
        directory = tempfile.TemporaryDirectory(dir=WORKSPACE_TEMP_DIR)
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "previous.json"
        path.write_text(
            json.dumps(
                {
                    "project": {"name": _project_name(scenario)},
                    "artifacts": {
                        "openapiSchema": str(SHARED / openapi),
                        "openuiSpecification": str(SHARED / openui),
                        "angularWorkspace": str(
                            Configuration(
                                _current_config(scenario)
                            ).project_config.angular_workspace
                        ),
                    },
                }
            ),
            encoding="utf-8",
        )
        return Configuration(path)

    def _incremental(self, scenario: str, previous: Configuration):
        # Identical OpenAPI files have an empty oasdiff result; no tool is needed.
        with patch("django_angular3.openapi_changes.run_oasdiff_diff", return_value={}):
            return self._translate(_current_config(scenario), previous)

    def test_a_scenario_without_a_change_gives_no_step(self) -> None:
        previous = self._previous(
            "09-no-change", "baseline.openapi.json", "base.openui.json"
        )
        # 09 selects the same documents as the previous state; only the project
        # name differs from the temporary previous configuration.
        change_set, _ = self._incremental("09-no-change", previous)

        self.assertFalse(change_set.domains[ChangeDomain.OPENAPI].has_changes)
        self.assertFalse(change_set.domains[ChangeDomain.OPENUI].has_changes)

    def test_adding_a_dashboard_to_an_application_without_children_updates_it(
        self,
    ) -> None:
        previous = self._previous(
            "06-add-dashboard", "baseline.openapi.json", "base.openui.json"
        )

        change_set, steps = self._incremental("06-add-dashboard", previous)

        self.assertFalse(change_set.domains[ChangeDomain.OPENAPI].has_changes)
        self.assertEqual(
            [c.subject for c in change_set.domains[ChangeDomain.OPENUI].changes],
            ["openui:/children"],
        )
        # The comparator reports the whole children list of the childless root, so
        # the page is part of an update of the Application (one application step).
        self.assertEqual(
            _step_keys(steps),
            [(2, "angular_app_scaffold", "update"), CHECK],
        )

    def test_selecting_another_openui_document_gives_only_the_final_check(self) -> None:
        scenario = SCENARIOS / "05-openui-source"
        previous = Configuration(
            scenario / "django-angular3-scenario-openui-source.previous.json"
        )

        change_set, steps = self._incremental("05-openui-source", previous)

        self.assertEqual(
            [
                c.subject
                for c in change_set.domains[ChangeDomain.PROJECT_CONFIG].changes
            ],
            ["artifacts.openuiSpecification"],
        )
        self.assertFalse(change_set.domains[ChangeDomain.OPENUI].has_changes)
        self.assertEqual(_step_keys(steps), [CHECK])

    def test_a_workspace_style_change_updates_the_workspace_foundation(self) -> None:
        baseline = json.loads(
            (SHARED / "static-config/workspace-style-scss.json").read_text("utf-8")
        )
        candidate = json.loads(
            (SHARED / "static-config/workspace-style-css.json").read_text("utf-8")
        )

        steps = translate_changes(compare_static_config(baseline, candidate), None)

        self.assertEqual(
            _step_keys(steps),
            [(1, "angular-workspace-foundation", "update"), CHECK],
        )

    @unittest.skipUnless(_oasdiff_available(), "oasdiff is not installed")
    def test_openapi_scenarios_derive_changes_that_are_never_dropped(self) -> None:
        for scenario in (
            "02-add-order",
            "03-schema-removal",
            "07-combined-change",
            "08-replace-resource",
            "10-config-openapi",
            "12-all-change-domains",
        ):
            with self.subTest(scenario=scenario):
                previous = self._previous(
                    scenario, "baseline.openapi.json", "base.openui.json"
                )
                change_set = ChangeDetector(
                    Configuration(_current_config(scenario)), previous
                ).detect_changes()
                changes = tuple(
                    c for d in ChangeDomain for c in change_set.domains[d].changes
                )
                try:
                    steps = translate_changes(changes, self.mapping)
                except CommandTranslationError:
                    continue  # an unsupported change fails explicitly, never silently
                self.assertEqual(steps[-1].name_id, "last-check")


if __name__ == "__main__":
    unittest.main()
