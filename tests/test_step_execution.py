"""Tests for the step-to-wrapper bridge and the execution of an app build."""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import django
from django.core.management import call_command
from django.core.management.base import CommandError

from django_angular3.changes import Change, ChangeDomain, ChangeOperation
from django_angular3.command_translation import AppBuildStep, translate_changes
from django_angular3.external_comparisons import compare_openui_files
from django_angular3.management.commands.build_app import (
    ChangeDetector,
    ChangeExecution,
    Configuration,
)
from django_angular3.ngdj_command_mapping import CommandMapping
from django_angular3.settings import load_angular_settings
from django_angular3.step_bridge import (
    CROSSWALK,
    STAGED_DOCUMENT_DIRECTORY,
    StepBridgeError,
    dasherize,
    resolve_steps,
    wrapper_for,
)
from django_angular3.step_execution import EVIDENCE_FILE_NAME
from tests.test_build_app import _change_set, _project_name_created
from tests.test_command_translation import FIXTURE_MAPPING, _openui_changes
from tests.workspace_temp import WORKSPACE_TEMP_DIR

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.test_settings")
django.setup()

REPOSITORY = Path(__file__).resolve().parent.parent
SHARED = REPOSITORY / "tests" / "fixtures" / "scenarios" / "shared"
ARCHITECTURE = REPOSITORY / "doc" / "ARCHITECTURE.md"

# The POC-shaped change: an application with a home page gains a dashboard page
# (scenario 06, ``add-dashboard``, over a base that already has a child).
_DASHBOARD_PAGE = json.loads(
    (SHARED / "dashboard.openui.json").read_text(encoding="utf-8")
)["children"][0]
_BASE_DOCUMENT = {
    "version": "0.12.0",
    "id": "root",
    "type": "Application",
    "children": [{"id": "home", "type": "EmptyPage"}],
}
_DASHBOARD_DOCUMENT = {
    **_BASE_DOCUMENT,
    "children": [*_BASE_DOCUMENT["children"], _DASHBOARD_PAGE],
}

# The base application plus every standalone element ngdj compiles without a wrapper.
_WIDGETS_DOCUMENT = {
    **_BASE_DOCUMENT,
    "children": [
        *_BASE_DOCUMENT["children"],
        {"id": "views", "type": "Tabs"},
        {"id": "confirmDelete", "type": "dialog"},
        {"id": "setupWizard", "type": "Stepper"},
        {"id": "orders", "type": "table"},
    ],
}

# A stand-in for the Angular CLI: it logs every call, creates the directory of
# ``ng new`` and fails when FAKE_NG_FAIL occurs in the call.
FAKE_NG = """\
import json
import os
import sys
from pathlib import Path

argv = sys.argv[1:]
with open(os.environ["FAKE_NG_LOG"], "a", encoding="utf-8") as log:
    log.write(json.dumps({"argv": argv, "cwd": os.getcwd()}) + "\\n")
if argv[:1] == ["new"]:
    directory = next(a for a in argv if a.startswith("--directory="))
    (Path.cwd() / directory.split("=", 1)[1]).mkdir(exist_ok=True)
marker = os.environ.get("FAKE_NG_FAIL")
if marker and marker in " ".join(argv):
    sys.stderr.write("simulated ng failure\\n")
    sys.exit(3)
"""


def _tree_digest(root: Path) -> dict[str, str]:
    """Every file and directory below ``root`` with a digest of its content."""
    return {
        path.relative_to(root).as_posix(): (
            hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "dir"
        )
        for path in sorted(root.rglob("*"))
    }


class CrosswalkTests(unittest.TestCase):
    def test_the_table_is_the_one_of_the_architecture(self) -> None:
        """The code copy of ``ARCHITECTURE.md`` §3.6.4.1 has no drift."""
        text = ARCHITECTURE.read_text(encoding="utf-8")
        section = text.split("##### 3.6.4.1 Automation naming crosswalk")[1]
        section = section.split("Contract uniqueness")[0]
        rows = {}
        for line in section.splitlines():
            if not line.startswith("| `"):
                continue
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            rows[cells[0].strip("`")] = tuple(
                tuple(re.findall(r"`([^`]+)`", cell)) for cell in cells[1:]
            )

        self.assertEqual(
            {
                row.concern_key: (row.wrappers, row.tools, row.skills)
                for row in CROSSWALK
            },
            rows,
        )

    def test_a_tool_name_and_a_skill_name_select_the_same_wrapper(self) -> None:
        step = _page_step()

        self.assertEqual(
            {
                wrapper_for(_with_name(step, name))
                for name in ("ngdj_add_page", "angular-page-composition")
            },
            {("angular.page", "ng_page")},
        )

    def test_the_workspace_wrapper_follows_the_operation(self) -> None:
        (step, *_) = translate_changes((_project_name_created(),))
        self.assertEqual(wrapper_for(step), ("angular.workspace", "ng_workspace"))
        self.assertEqual(
            wrapper_for(replace(step, change_op="update")),
            ("angular.workspace", "ng_workspace_modify"),
        )

    def test_a_name_outside_the_crosswalk_is_refused(self) -> None:
        (step, *_) = translate_changes((_project_name_created(),))
        with self.assertRaisesRegex(StepBridgeError, "not in the automation naming"):
            wrapper_for(_with_name(step, "made-up-step"))

    def test_a_concern_without_a_wrapper_is_refused(self) -> None:
        (step, *_) = translate_changes((_project_name_created(),))
        with self.assertRaisesRegex(StepBridgeError, "has no operator wrapper"):
            wrapper_for(_with_name(step, "ngdj_add_feature"))

    def test_the_last_gate_runs_the_application_build(self) -> None:
        steps = translate_changes((_project_name_created(),))
        self.assertEqual(wrapper_for(steps[-1]), (None, "ng_build"))


def _mapping() -> CommandMapping:
    return CommandMapping(json.loads(FIXTURE_MAPPING.read_text(encoding="utf-8")))


def _page_step():
    """The ``ngdj_add_page`` step of a real OpenUI comparison."""
    return translate_changes(
        _openui_changes([], [{"id": "home", "type": "DashboardPage"}]), _mapping()
    )[0]


def _with_name(step: AppBuildStep, name: str) -> AppBuildStep:
    return replace(step, name_id=name)


class _Project:
    """A temporary project whose scenario documents live outside its workspace."""

    def __init__(self, test: unittest.TestCase, *, document_in_workspace=False) -> None:
        directory = tempfile.TemporaryDirectory(dir=WORKSPACE_TEMP_DIR)
        test.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.workspace = self.root / "angular"
        self.workspace.mkdir()
        self.document = (
            self.workspace / "app.openui.json"
            if document_in_workspace
            else self.root / "app.openui.json"
        )
        self.document.write_text(json.dumps(_DASHBOARD_DOCUMENT), encoding="utf-8")
        shutil.copyfile(
            SHARED / "baseline.openapi.json", self.root / "api.openapi.json"
        )
        self.config = self._configuration("current", self.document)
        self.previous = self._configuration("previous", self.root / "base.openui.json")
        (self.root / "base.openui.json").write_text(
            json.dumps(_BASE_DOCUMENT), encoding="utf-8"
        )
        self.project_config = self.config.project_config
        self._install_ngdj()
        self._install_fake_ng(test)

    def _configuration(self, name: str, document: Path) -> Configuration:
        path = self.root / f"{name}.json"
        path.write_text(
            json.dumps(
                {
                    "project": {"name": "shop"},
                    "artifacts": {
                        "openapiSchema": "api.openapi.json",
                        "openuiSpecification": str(document.relative_to(self.root)),
                        "angularWorkspace": "angular",
                    },
                }
            ),
            encoding="utf-8",
        )
        return Configuration(path)

    def _install_ngdj(self) -> None:
        fixture = FIXTURE_MAPPING.parent
        package = self.workspace / "node_modules" / "angular-django2"
        (package / "schematics").mkdir(parents=True)
        shutil.copyfile(fixture / "package.json", package / "package.json")
        for name in ("command-mapping.json", "command-mapping.schema.json"):
            shutil.copyfile(fixture / name, package / "schematics" / name)

    def _install_fake_ng(self, test: unittest.TestCase) -> None:
        tools = self.root / "tools"
        tools.mkdir()
        script = tools / "fake_ng.py"
        script.write_text(FAKE_NG, encoding="utf-8")
        if os.name == "nt":
            ng = tools / "ng.cmd"
            ng.write_text(f'@"{sys.executable}" "{script}" %*\n', encoding="utf-8")
        else:
            ng = tools / "ng"
            ng.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{script}" "$@"\n')
            ng.chmod(0o755)
        self.log = self.root / "ng.log"
        self.settings = load_angular_settings({"ng_executable": str(ng)})
        environment = patch.dict(os.environ, {"FAKE_NG_LOG": str(self.log)})
        environment.start()
        test.addCleanup(environment.stop)

    def calls(self) -> list[list[str]]:
        if not self.log.is_file():
            return []
        lines = self.log.read_text(encoding="utf-8").splitlines()
        return [json.loads(line)["argv"] for line in lines]

    def change_set(self, **extra):
        pages = compare_openui_files(self.root / "base.openui.json", self.document)
        return _change_set(
            project_config=(_project_name_created(),), openui=pages, **extra
        )

    def run_build(self, change_set, **options):
        stdout = io.StringIO()
        with (
            patch.object(ChangeDetector, "detect_changes", return_value=change_set),
            patch(
                "django_angular3.management.commands.build_app.load_angular_settings",
                return_value=self.settings,
            ),
        ):
            call_command(
                "build_app",
                current_config=str(self.project_config.config_path),
                previous_config=str(self.previous.project_config.config_path),
                output=str(self.root / "build"),
                stdout=stdout,
                **options,
            )
        return stdout.getvalue()


class StepResolutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.project = _Project(self)

    def resolve(self, change_set, mapping=None):
        steps = translate_changes(
            tuple(
                change
                for result in change_set.domains.values()
                for change in result.changes
            ),
            _mapping(),
        )
        return resolve_steps(steps, self.project.project_config, mapping or _mapping())

    def test_a_page_step_carries_the_command_and_its_resolved_parameters(self) -> None:
        steps = self.resolve(self.project.change_set())

        page = next(step for step in steps if step.name_id == "ngdj_add_page")
        self.assertEqual(
            (page.concern_key, page.command, page.ngdj_command),
            ("angular.page", "ng_page", "page"),
        )
        self.assertEqual(
            dict(page.parameters),
            {
                "name": "dashboard-page",
                "target_path": "src/app/features/dashboard-page",
                "project": "shop",
                "document": f"{STAGED_DOCUMENT_DIRECTORY}/app.openui.json",
                "node_id": "dashboardPage",
            },
        )
        self.assertEqual(page.unresolved, ())

    def test_foundation_steps_resolve_without_an_openui_element(self) -> None:
        steps = self.resolve(_change_set(project_config=(_project_name_created(),)))

        self.assertEqual(
            [(step.command, dict(step.parameters)) for step in steps],
            [
                ("ng_workspace", {}),
                ("ng_gen_app", {"app_name": "shop"}),
                ("ng_build", {}),
            ],
        )

    def test_a_document_inside_the_workspace_is_read_in_place(self) -> None:
        project = _Project(self, document_in_workspace=True)
        steps = translate_changes(
            tuple(
                compare_openui_files(
                    project.root / "base.openui.json", project.document
                )
            ),
            _mapping(),
        )

        (page, _gate) = resolve_steps(steps, project.project_config, _mapping())

        self.assertEqual(page.parameters["document"], "app.openui.json")

    def test_a_data_service_step_leaves_the_resource_unresolved(self) -> None:
        change_set = _change_set(
            openapi=(
                Change(
                    ChangeDomain.OPENAPI,
                    "path:/customers",
                    "/paths/~1customers",
                    ChangeOperation.CREATE,
                    None,
                    {},
                ),
            )
        )

        steps = self.resolve(change_set)

        service = next(step for step in steps if step.command == "ng_data_service")
        self.assertEqual(service.unresolved, ("resource",))
        client = next(step for step in steps if step.command == "ng_openapi_gen")
        self.assertEqual(client.unresolved, ())

    def test_an_option_the_ngdj_command_does_not_accept_is_refused(self) -> None:
        document = json.loads(FIXTURE_MAPPING.read_text(encoding="utf-8"))
        page = document["ui"]["commands"]["page"]
        page["parameters"] = [p for p in page["parameters"] if p["name"] != "nodeId"]

        with self.assertRaisesRegex(StepBridgeError, "has no parameter nodeId"):
            self.resolve(self.project.change_set(), CommandMapping(document))

    def test_a_wrapper_without_an_invocation_builder_is_refused(self) -> None:
        change = Change(
            ChangeDomain.STATIC_CONFIG,
            "drfSpectacular.settings.TITLE",
            "/drfSpectacular/settings/TITLE",
            ChangeOperation.UPDATE,
            "a",
            "b",
        )
        steps = translate_changes((change,))

        with self.assertRaisesRegex(StepBridgeError, "no invocation builder"):
            resolve_steps(steps, self.project.project_config)

    def test_a_widget_step_runs_the_ngdj_command_of_the_mapping_without_a_wrapper(
        self,
    ) -> None:
        self.project.document.write_text(
            json.dumps(_WIDGETS_DOCUMENT), encoding="utf-8"
        )

        steps = self.resolve(self.project.change_set())

        widgets = {
            step.name_id: step for step in steps if step.name_id.startswith("ngdj_add_")
        }
        self.assertEqual(
            {name: (s.concern_key, s.command) for name, s in widgets.items()},
            {
                "ngdj_add_tabs": ("angular.tabs", "angular-django2:tabs"),
                "ngdj_add_dialog": ("angular.dialog", "angular-django2:dialog"),
                "ngdj_add_stepper": ("angular.stepper", "angular-django2:stepper"),
                "ngdj_add_table": ("angular.table", "angular-django2:table"),
            },
        )
        self.assertEqual(
            dict(widgets["ngdj_add_tabs"].parameters),
            {
                "project": "shop",
                "document": f"{STAGED_DOCUMENT_DIRECTORY}/app.openui.json",
                "node_id": "views",
            },
        )

    def test_a_widget_step_is_refused_when_the_command_lacks_an_option(self) -> None:
        self.project.document.write_text(
            json.dumps(_WIDGETS_DOCUMENT), encoding="utf-8"
        )
        document = json.loads(FIXTURE_MAPPING.read_text(encoding="utf-8"))
        tabs = document["ui"]["commands"]["tabs"]
        tabs["parameters"] = [p for p in tabs["parameters"] if p["name"] != "project"]

        with self.assertRaisesRegex(StepBridgeError, "has no parameter project"):
            self.resolve(self.project.change_set(), CommandMapping(document))

    def test_element_ids_are_dasherized_as_ngdj_names_them(self) -> None:
        self.assertEqual(
            [dasherize(i) for i in ("home", "dashboardPage", "order_list", "A1b")],
            ["home", "dashboard-page", "order-list", "a1b"],
        )


class DryRunTests(unittest.TestCase):
    def setUp(self) -> None:
        self.project = _Project(self)

    def test_the_dry_run_prints_order_command_parameters_and_reason(self) -> None:
        report = json.loads(
            self.project.run_build(self.project.change_set(), dry_run=True)
        )

        self.assertEqual(
            [(s["stage"], s["step"], s["command"]) for s in report["steps"]],
            [
                (1, "angular-workspace-foundation", "ng_workspace"),
                (2, "angular-app-composition", "ng_gen_app"),
                (10, "ngdj_add_page", "ng_page"),
                (12, "last-check", "ng_build"),
            ],
        )
        page = report["steps"][2]
        self.assertEqual(page["parameters"]["node_id"], "dashboardPage")
        self.assertEqual(page["parameters"]["name"], "dashboard-page")
        self.assertIn("ngdj page compiles DashboardPage dashboardPage", page["reason"])
        self.assertEqual(report["dryRun"], True)

    def test_the_evidence_pins_the_ngdj_package_and_mapping_versions(self) -> None:
        report = json.loads(
            self.project.run_build(self.project.change_set(), dry_run=True)
        )

        self.assertEqual(
            report["ngdj"],
            {
                "package": "angular-django2@0.7.0",
                "mappingVersion": 1,
                "openuiSpecVersion": "0.12.1",
            },
        )

    def test_the_dry_run_changes_nothing(self) -> None:
        before = _tree_digest(self.project.root)

        self.project.run_build(self.project.change_set(), dry_run=True)

        self.assertEqual(_tree_digest(self.project.root), before)
        self.assertEqual(self.project.calls(), [])
        self.assertFalse((self.project.root / "build").exists())
        self.assertFalse((self.project.workspace / STAGED_DOCUMENT_DIRECTORY).exists())

    def test_the_dry_run_lists_what_is_unresolved(self) -> None:
        change_set = _change_set(
            openapi=(
                Change(
                    ChangeDomain.OPENAPI,
                    "path:/customers",
                    "/paths/~1customers",
                    ChangeOperation.CREATE,
                    None,
                    {},
                ),
            )
        )

        report = json.loads(self.project.run_build(change_set, dry_run=True))

        service = next(s for s in report["steps"] if s["command"] == "ng_data_service")
        self.assertEqual(service["unresolved"], ["resource"])

    def test_a_dry_run_still_refuses_what_has_no_wrapper(self) -> None:
        change = Change(
            ChangeDomain.STATIC_CONFIG,
            "drfSpectacular.settings.TITLE",
            "/drfSpectacular/settings/TITLE",
            ChangeOperation.UPDATE,
            "a",
            "b",
        )

        with self.assertRaisesRegex(CommandError, "Failed to resolve steps"):
            self.project.run_build(_change_set(static_config=(change,)), dry_run=True)


class RealRunTests(unittest.TestCase):
    def setUp(self) -> None:
        self.project = _Project(self)

    def dry_run_steps(self) -> list[tuple[str, str]]:
        report = json.loads(
            self.project.run_build(self.project.change_set(), dry_run=True)
        )
        return [(s["command"], s["step"]) for s in report["steps"]]

    def test_a_real_run_executes_the_steps_of_the_dry_run(self) -> None:
        previewed = self.dry_run_steps()

        self.project.run_build(self.project.change_set())

        evidence = json.loads(
            (self.project.root / "build" / EVIDENCE_FILE_NAME).read_text("utf-8")
        )
        self.assertEqual(
            [(s["command"], s["step"]) for s in evidence["steps"]], previewed
        )
        self.assertEqual({s["status"] for s in evidence["steps"]}, {"succeeded"})
        self.assertFalse(evidence["dryRun"])

    def test_the_wrappers_call_ng_in_step_order_in_the_workspace(self) -> None:
        self.project.run_build(self.project.change_set())

        calls = self.project.calls()
        self.assertEqual(
            [c[0] if c[0] != "generate" else c[1] for c in calls],
            [
                "new",
                "config",
                "config",
                "config",
                "add",
                "angular-django2:workspace-setup",
                "angular-django2:material-app",
                "angular-django2:page",
                "build",
            ],
        )
        page = next(c for c in calls if c[:2] == ["generate", "angular-django2:page"])
        self.assertEqual(
            page[2:],
            [
                "dashboard-page",
                "--path=src/app/features/dashboard-page",
                "--project=shop",
                f"--document={STAGED_DOCUMENT_DIRECTORY}/app.openui.json",
                "--node-id=dashboardPage",
            ],
        )

    def test_widgets_are_generated_by_the_ngdj_schematic_before_the_pages(self) -> None:
        self.project.document.write_text(
            json.dumps(_WIDGETS_DOCUMENT), encoding="utf-8"
        )

        self.project.run_build(self.project.change_set())

        generated = [c for c in self.project.calls() if c[:1] == ["generate"]]
        self.assertEqual(
            [c[1] for c in generated[-4:]],
            [
                "angular-django2:dialog",
                "angular-django2:stepper",
                "angular-django2:table",
                "angular-django2:tabs",
            ],
        )
        tabs = next(c for c in generated if c[1] == "angular-django2:tabs")
        self.assertEqual(
            tabs[2:],
            [
                "--project=shop",
                f"--document={STAGED_DOCUMENT_DIRECTORY}/app.openui.json",
                "--node-id=views",
            ],
        )

    def test_the_document_is_staged_in_the_workspace_for_ngdj(self) -> None:
        self.project.run_build(self.project.change_set())

        staged = self.project.workspace / STAGED_DOCUMENT_DIRECTORY / "app.openui.json"
        self.assertEqual(staged.read_bytes(), self.project.document.read_bytes())

    def test_the_evidence_pins_the_ngdj_package_and_mapping_versions(self) -> None:
        self.project.run_build(self.project.change_set())

        evidence = json.loads(
            (self.project.root / "build" / EVIDENCE_FILE_NAME).read_text("utf-8")
        )
        self.assertEqual(evidence["ngdj"]["package"], "angular-django2@0.7.0")
        self.assertEqual(evidence["ngdj"]["mappingVersion"], 1)
        self.assertEqual(evidence["ngdj"]["openuiSpecVersion"], "0.12.1")
        call = evidence["steps"][2]["invocations"][0]
        self.assertEqual(call["returncode"], 0)

    def test_the_run_halts_at_the_first_failure(self) -> None:
        with (
            patch.dict(os.environ, {"FAKE_NG_FAIL": "angular-django2:material-app"}),
            self.assertRaisesRegex(
                CommandError,
                r"(?s)Step angular-app-composition \(ng_gen_app, project.name\) "
                r"failed: .*simulated ng failure.*The remaining steps were skipped",
            ),
        ):
            self.project.run_build(self.project.change_set())

        calls = self.project.calls()
        self.assertEqual(calls[-1][:2], ["generate", "angular-django2:material-app"])
        self.assertNotIn("angular-django2:page", [c[1] for c in calls if len(c) > 1])
        self.assertNotIn("build", [c[0] for c in calls])
        evidence = json.loads(
            (self.project.root / "build" / EVIDENCE_FILE_NAME).read_text("utf-8")
        )
        self.assertEqual(
            [s["status"] for s in evidence["steps"]],
            ["succeeded", "failed", "skipped", "skipped"],
        )
        self.assertEqual(evidence["steps"][1]["invocations"][0]["returncode"], 3)

    def test_a_failing_invocation_stops_the_remaining_ones_of_its_step(self) -> None:
        with (
            patch.dict(os.environ, {"FAKE_NG_FAIL": "config cli.packageManager"}),
            self.assertRaises(CommandError),
        ):
            self.project.run_build(self.project.change_set())

        self.assertEqual([c[0] for c in self.project.calls()], ["new", "config"])

    def test_an_unresolved_parameter_stops_the_run_before_anything_runs(self) -> None:
        change_set = self.project.change_set(
            openapi=(
                Change(
                    ChangeDomain.OPENAPI,
                    "path:/customers",
                    "/paths/~1customers",
                    ChangeOperation.CREATE,
                    None,
                    {},
                ),
            )
        )
        before = _tree_digest(self.project.root)

        with self.assertRaisesRegex(
            CommandError, r"nothing was executed: ng_data_service .* needs resource"
        ):
            self.project.run_build(change_set)

        self.assertEqual(self.project.calls(), [])
        self.assertEqual(_tree_digest(self.project.root), before)

    def test_force_is_refused_rather_than_ignored(self) -> None:
        with self.assertRaisesRegex(CommandError, "--force start-from-scratch"):
            ChangeExecution().execute(
                self.project.change_set(),
                self.project.project_config,
                str(self.project.root / "build"),
                True,
                True,
                settings=self.project.settings,
            )


if __name__ == "__main__":
    unittest.main()
