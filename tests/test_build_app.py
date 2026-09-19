import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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
)
from tests.workspace_temp import WORKSPACE_TEMP_DIR


class OpenUIConfigurationTests(unittest.TestCase):
    def test_load_stores_the_openui_document(self) -> None:
        document = {"version": "0.2.0", "id": "root", "type": "Application"}
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
                subject="openui:/children/0",
                path="/children/0",
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
            subject="openui:/children/0",
            path="/children/0",
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
    def test_returns_an_ordered_command_plan(self) -> None:
        change_set = ChangeSet(
            baseline={},
            candidate={},
            domains={
                ChangeDomain.STATIC_CONFIG: ChangeDomainResult(
                    ChangeDomain.STATIC_CONFIG
                ),
                ChangeDomain.PROJECT_CONFIG: ChangeDomainResult(
                    ChangeDomain.PROJECT_CONFIG
                ),
                ChangeDomain.OPENAPI: ChangeDomainResult(
                    ChangeDomain.OPENAPI,
                    (
                        Change(
                            domain=ChangeDomain.OPENAPI,
                            subject="schema:Customer",
                            path="/components/schemas/Customer",
                            operation=ChangeOperation.UPDATE,
                            before={},
                            after={},
                        ),
                    ),
                ),
                ChangeDomain.OPENUI: ChangeDomainResult(ChangeDomain.OPENUI),
            },
        )

        commands = ChangeExecution(change_set).translate_change_set()

        self.assertEqual(
            [command.name for command in commands],
            [
                "angular-api-integration",
                "angular-data-service-composition",
                "angular-page-composition",
                "terminal-validation",
            ],
        )

    def test_returns_no_commands_for_an_empty_change_set(self) -> None:
        change_set = ChangeSet(
            baseline={},
            candidate={},
            domains={domain: ChangeDomainResult(domain) for domain in ChangeDomain},
        )

        self.assertEqual(ChangeExecution(change_set).translate_change_set(), ())


if __name__ == "__main__":
    unittest.main()
