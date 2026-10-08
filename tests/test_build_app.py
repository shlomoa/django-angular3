import io
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import django
from django.core.management import call_command
from django.core.management.base import CommandError

from django_angular3.changes import (
    Change,
    ChangeDomain,
    ChangeDomainResult,
    ChangeOperation,
    ChangeSet,
)
from django_angular3.external_comparisons import ExternalComparisonError
from django_angular3.management.commands.build_app import (
    ChangeDetector,
    ChangeExecution,
    Configuration,
    OpenUIConfiguration,
    load_ngdj_mapping,
)
from django_angular3.ngdj_command_mapping import CommandMapping
from tests.test_command_translation import FIXTURE_MAPPING, _openui_changes
from tests.workspace_temp import WORKSPACE_TEMP_DIR

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.test_settings")
django.setup()


class OpenUIConfigurationTests(unittest.TestCase):
    def test_load_stores_the_openui_document(self) -> None:
        document = {"version": "0.12.0", "id": "root", "type": "Application"}
        with tempfile.TemporaryDirectory(dir=WORKSPACE_TEMP_DIR) as temporary_directory:
            path = Path(temporary_directory) / "document.openui.json"
            path.write_text(json.dumps(document), encoding="utf-8")

            configuration = OpenUIConfiguration(path)
            configuration.load()

        self.assertEqual(configuration.openui_spec, document)

    def test_load_reports_openui_document_errors(self) -> None:
        with tempfile.TemporaryDirectory(dir=WORKSPACE_TEMP_DIR) as temporary_directory:
            path = Path(temporary_directory) / "invalid.openui.json"
            path.write_text("{", encoding="utf-8")

            with self.assertRaisesRegex(CommandError, "cannot load JSON document"):
                OpenUIConfiguration(path).load()


class TestableChangeDetector(ChangeDetector):
    def diff_openapi_schemas(self) -> tuple[Change, ...]:
        return self._diff_openapi_schemas()

    def diff_openui_specifications(self) -> tuple[Change, ...]:
        return self._diff_openui_specifications()


class OpenAPIDiffTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory(dir=WORKSPACE_TEMP_DIR)
        self.addCleanup(self.temporary_directory.cleanup)
        root = Path(self.temporary_directory.name)
        self.current_config = self._configuration(root, "current")
        self.previous_config = self._configuration(root, "previous")
        self.detector = TestableChangeDetector(
            self.current_config,
            self.previous_config,
        )

    def _configuration(self, root: Path, name: str) -> Configuration:
        configuration_path = root / f"{name}.json"
        configuration_path.write_text(
            json.dumps(
                {
                    "project": {"name": name},
                    "artifacts": {
                        "openapiSchema": f"{name}.openapi.json",
                        "openuiSpecification": f"{name}.openui.json",
                        "angularWorkspace": f"{name}-angular",
                    },
                }
            ),
            encoding="utf-8",
        )
        return Configuration(configuration_path)

    def test_delegates_openapi_comparison_with_previous_and_current_schemas(
        self,
    ) -> None:
        expected = ()
        with patch(
            "django_angular3.management.commands.build_app.compare_openapi_files",
            return_value=expected,
        ) as compare:
            self.assertEqual(self.detector.diff_openapi_schemas(), expected)

        root = Path(self.temporary_directory.name)
        compare.assert_called_once_with(
            root / "previous.openapi.json",
            root / "current.openapi.json",
        )

    def test_normalizes_openapi_comparison_errors_as_command_errors(self) -> None:
        with (
            patch(
                "django_angular3.management.commands.build_app.compare_openapi_files",
                side_effect=ExternalComparisonError("invalid oasdiff JSON"),
            ),
            self.assertRaisesRegex(CommandError, "Failed to diff OpenAPI schemas"),
        ):
            self.detector.diff_openapi_schemas()

    def test_delegates_openui_comparison_with_previous_and_current_specs(self) -> None:
        expected = (
            Change(
                domain=ChangeDomain.OPENUI,
                subject="openui:/children/dashboard",
                path="/children/dashboard",
                operation=ChangeOperation.CREATE,
                before=None,
                after={"id": "dashboard"},
            ),
        )
        with patch(
            "django_angular3.management.commands.build_app.compare_openui_files",
            return_value=expected,
        ) as compare:
            self.assertEqual(self.detector.diff_openui_specifications(), expected)

        root = Path(self.temporary_directory.name)
        compare.assert_called_once_with(
            root / "previous.openui.json",
            root / "current.openui.json",
        )

    def test_detect_changes_returns_a_canonical_change_set(self) -> None:
        project_change = Change(
            domain=ChangeDomain.PROJECT_CONFIG,
            subject="project.name",
            path="/project/name",
            operation=ChangeOperation.UPDATE,
            before="previous",
            after="current",
        )
        openapi_change = Change(
            domain=ChangeDomain.OPENAPI,
            subject="path:/items",
            path="/paths/~1items",
            operation=ChangeOperation.CREATE,
            before=None,
            after={},
        )
        openui_change = Change(
            domain=ChangeDomain.OPENUI,
            subject="openui:/children/dashboard",
            path="/children/dashboard",
            operation=ChangeOperation.CREATE,
            before=None,
            after={"id": "dashboard"},
        )
        with (
            patch(
                "django_angular3.management.commands.build_app.compare_project_config",
                return_value=(project_change,),
            ),
            patch(
                "django_angular3.management.commands.build_app.compare_openapi_files",
                return_value=(openapi_change,),
            ),
            patch(
                "django_angular3.management.commands.build_app.compare_openui_files",
                return_value=(openui_change,),
            ),
        ):
            changes = self.detector.detect_changes()

        self.assertIsInstance(changes, ChangeSet)
        self.assertTrue(changes.has_changes)
        self.assertEqual(
            changes.domains[ChangeDomain.STATIC_CONFIG].changes,
            (),
        )
        self.assertEqual(
            changes.domains[ChangeDomain.PROJECT_CONFIG].changes,
            (project_change,),
        )
        self.assertEqual(
            changes.domains[ChangeDomain.OPENAPI].changes,
            (openapi_change,),
        )
        self.assertEqual(
            changes.domains[ChangeDomain.OPENUI].changes,
            (openui_change,),
        )


class ChangeExecutionTranslationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.mapping = CommandMapping(
            json.loads(FIXTURE_MAPPING.read_text(encoding="utf-8"))
        )

    def test_returns_ordered_commands(self) -> None:
        change_set = _change_set(
            openapi=(
                Change(
                    domain=ChangeDomain.OPENAPI,
                    subject="path:/customers",
                    path="/paths/~1customers",
                    operation=ChangeOperation.CREATE,
                    before=None,
                    after={},
                ),
            ),
            openui=_openui_changes([], [{"id": "customers", "type": "DashboardPage"}]),
        )

        commands = ChangeExecution()._translate_change_set(change_set, self.mapping)

        self.assertEqual(
            [command.name_id for command in commands],
            [
                "angular_api_client_generate",
                "ngdj_add_data_service",
                "ngdj_add_page",
                "last-check",
            ],
        )

    def test_an_unsupported_schema_update_is_a_command_error(self) -> None:
        change_set = _change_set(
            openapi=(
                Change(
                    domain=ChangeDomain.OPENAPI,
                    subject="schema:Customer",
                    path="/components/schemas/Customer",
                    operation=ChangeOperation.UPDATE,
                    before={},
                    after={},
                ),
            )
        )

        with self.assertRaisesRegex(
            CommandError,
            r"Failed to translate changes: ngdj does not support update of the "
            r"data services that depend on schema:Customer",
        ):
            ChangeExecution()._translate_change_set(change_set, self.mapping)

    def test_returns_no_commands_for_an_empty_change_set(self) -> None:
        change_set = ChangeSet(
            baseline={},
            candidate={},
            domains={domain: ChangeDomainResult(domain) for domain in ChangeDomain},
        )

        self.assertEqual(ChangeExecution()._translate_change_set(change_set), ())


def _change_set(**changes: tuple[Change, ...]) -> ChangeSet:
    """A ChangeSet whose domains hold the given Changes (keyed by domain value)."""
    return ChangeSet(
        baseline={},
        candidate={},
        domains={
            domain: ChangeDomainResult(domain, changes.get(domain.value, ()))
            for domain in ChangeDomain
        },
    )


def _project_name_created() -> Change:
    return Change(
        domain=ChangeDomain.PROJECT_CONFIG,
        subject="project.name",
        path="/project/name",
        operation=ChangeOperation.CREATE,
        before=None,
        after="current",
    )


class BuildAppTranslationTests(unittest.TestCase):
    """The command mapping reaches the translation, and a dry run reports the steps."""

    def setUp(self) -> None:
        temporary_directory = tempfile.TemporaryDirectory(dir=WORKSPACE_TEMP_DIR)
        self.addCleanup(temporary_directory.cleanup)
        self.root = Path(temporary_directory.name)
        self.current = self._configuration("current")
        self.previous = self._configuration("previous")
        self.mapping = CommandMapping(
            json.loads(FIXTURE_MAPPING.read_text(encoding="utf-8"))
        )

    def _configuration(self, name: str) -> Configuration:
        path = self.root / f"{name}.json"
        path.write_text(
            json.dumps(
                {
                    "project": {"name": name},
                    "artifacts": {
                        "openapiSchema": f"{name}.openapi.json",
                        "openuiSpecification": f"{name}.openui.json",
                        "angularWorkspace": f"{name}-angular",
                    },
                }
            ),
            encoding="utf-8",
        )
        return Configuration(path)

    def install_ngdj(self) -> None:
        """Install the fixture package where the current workspace expects it."""
        fixture = FIXTURE_MAPPING.parent
        package = self.current.project_config.angular_workspace / (
            "node_modules/angular-django2"
        )
        (package / "schematics").mkdir(parents=True)
        shutil.copyfile(fixture / "package.json", package / "package.json")
        for name in ("command-mapping.json", "command-mapping.schema.json"):
            shutil.copyfile(fixture / name, package / "schematics" / name)

    def dry_run(self, change_set: ChangeSet) -> dict:
        stdout = io.StringIO()
        with patch.object(ChangeDetector, "detect_changes", return_value=change_set):
            call_command(
                "build_app",
                current_config=str(self.current.project_config.config_path),
                previous_config=str(self.previous.project_config.config_path),
                dry_run=True,
                stdout=stdout,
            )
        return json.loads(stdout.getvalue())

    def test_changes_that_need_no_mapping_do_not_require_the_package(self) -> None:
        change_set = _change_set(project_config=(_project_name_created(),))

        self.assertIsNone(load_ngdj_mapping(change_set, self.current.project_config))

    def test_openui_and_openapi_changes_load_the_installed_mapping(self) -> None:
        self.install_ngdj()
        openui = _openui_changes([], [{"id": "home", "type": "DashboardPage"}])

        mapping = load_ngdj_mapping(
            _change_set(openui=openui), self.current.project_config
        )

        assert mapping is not None
        self.assertEqual(mapping.mapping_version, 1)

    def test_a_missing_package_is_reported_with_how_to_install_it(self) -> None:
        openui = _openui_changes([], [{"id": "home", "type": "DashboardPage"}])

        with self.assertRaisesRegex(
            CommandError,
            r"Cannot translate the OpenUI and OpenAPI changes.*Install "
            r"angular-django2@0\.7\.0",
        ):
            load_ngdj_mapping(_change_set(openui=openui), self.current.project_config)

    def test_the_mapping_reaches_the_translation(self) -> None:
        openui = _openui_changes([], [{"id": "home", "type": "DashboardPage"}])

        steps = ChangeExecution()._translate_change_set(
            _change_set(openui=openui), self.mapping
        )

        self.assertEqual(
            [step.name_id for step in steps], ["ngdj_add_page", "last-check"]
        )

    def test_a_dry_run_returns_the_steps_without_running_them(self) -> None:
        change_set = _change_set(project_config=(_project_name_created(),))

        with patch(
            "django_angular3.step_execution.command_execution.run_command"
        ) as run_command:
            evidence = ChangeExecution().execute(
                change_set, self.current.project_config, "build", True, False
            )

        run_command.assert_not_called()
        self.assertEqual(
            [step.name_id for step in evidence.steps],
            ["angular-workspace-foundation", "angular-app-composition", "last-check"],
        )

    def test_the_dry_run_command_prints_the_ordered_steps(self) -> None:
        report = self.dry_run(_change_set(project_config=(_project_name_created(),)))

        self.assertEqual(
            report["projectConfig"], str(self.current.project_config.config_path)
        )
        self.assertEqual(
            [(step["stage"], step["step"], step["mode"]) for step in report["steps"]],
            [
                (1, "angular-workspace-foundation", "create"),
                (2, "angular-app-composition", "create"),
                (12, "last-check", "validate"),
            ],
        )
        self.assertEqual(report["steps"][0]["target"], "project.name")
        self.assertIn("Required by project_config create", report["steps"][0]["reason"])

    def test_the_dry_run_of_an_empty_change_set_prints_no_steps(self) -> None:
        report = self.dry_run(_change_set())

        self.assertEqual(report["steps"], [])

    def test_the_dry_run_translates_openui_changes_with_the_installed_mapping(
        self,
    ) -> None:
        self.install_ngdj()
        openui = _openui_changes([], [{"id": "home", "type": "DashboardPage"}])

        report = self.dry_run(_change_set(openui=openui))

        step = report["steps"][0]
        self.assertEqual(
            (step["stage"], step["step"], step["mode"], step["nodeId"], step["domain"]),
            (10, "ngdj_add_page", "create", "home", "openui"),
        )
        self.assertIn("ngdj page compiles DashboardPage home", step["reason"])

    def test_the_dry_run_reports_an_unsupported_change_as_a_command_error(
        self,
    ) -> None:
        self.install_ngdj()
        openui = _openui_changes([{"id": "signup", "type": "Form"}], [])

        with self.assertRaisesRegex(
            CommandError,
            r"Failed to translate changes: ngdj does not support delete of OpenUI "
            r"node type Form",
        ):
            self.dry_run(_change_set(openui=openui))


if __name__ == "__main__":
    unittest.main()
