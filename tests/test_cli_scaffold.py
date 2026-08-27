import json
import tempfile
import tomllib
import unittest
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast
from unittest.mock import patch

from django_angular3.cli import _run_install_tutorial
from django_angular3.config import (
    ConfigError,
    discover_project_config_path,
    load_project_config,
    project_config_path,
)
from django_angular3.config_changes import compare_static_config
from django_angular3.documents import load_document
from django_angular3.validation import (
    validate_openapi_document,
    validate_openui_document,
    validate_project_config,
)
from tests.openapi_fixtures import valid_openapi_document
from tests.workspace_temp import WORKSPACE_TEMP_DIR

ROOT = Path(__file__).resolve().parent.parent
ARTIFACT_FIXTURES = ROOT / "tests" / "fixtures" / "artifacts"
TEST_PROJECT_CONFIG_FILENAME = "django-angular3-project.json"
TUTORIAL_PROJECT_CONFIG_FILENAME = "django-angular3-simple_crm.json"


def _example_project_config_path(example_directory: Path) -> Path:
    config_paths = [
        path
        for path in example_directory.glob("django-angular3-*.json")
        if path.name != "django-angular3.json"
        and not path.name.endswith(".previous.json")
    ]
    if len(config_paths) != 1:
        raise AssertionError(
            "Expected one project configuration in "
            f"{example_directory}, found {config_paths}."
        )
    return config_paths[0]


class ScaffoldTests(unittest.TestCase):
    def test_standalone_project_config_discovery_uses_current_directory(self) -> None:
        with tempfile.TemporaryDirectory(dir=WORKSPACE_TEMP_DIR) as tmp:
            project_root = Path(tmp)
            with patch("django_angular3.config.Path.cwd", return_value=project_root):
                self.assertEqual(
                    discover_project_config_path(),
                    project_root / project_config_path(),
                )

    def test_example_openapi_document_is_valid(self) -> None:
        document = load_document(ARTIFACT_FIXTURES / "openapi" / "example.openapi.json")
        self.assertEqual(validate_openapi_document(document), [])

    def test_example_openui_document_is_valid(self) -> None:
        document = load_document(ARTIFACT_FIXTURES / "openui" / "example.openui.json")
        self.assertEqual(validate_openui_document(document), [])

    def test_tutorial_openui_document_is_valid(self) -> None:
        document = load_document(
            ROOT / "django_angular3" / "examples" / "01_simple_crm" / "app.openui.json"
        )
        self.assertEqual(validate_openui_document(document), [])

    def test_tutorial_project_config_is_valid(self) -> None:
        config = load_project_config(
            ROOT
            / "django_angular3"
            / "examples"
            / "01_simple_crm"
            / TUTORIAL_PROJECT_CONFIG_FILENAME
        )
        self.assertEqual(validate_project_config(config), [])

    def test_shipped_static_configs_pin_ngdj_package(self) -> None:
        for static_config_path in (
            ROOT / "django-angular3.json",
            ROOT
            / "django_angular3"
            / "templates"
            / "django_angular3"
            / "django-angular3.json",
            ROOT
            / "django_angular3"
            / "examples"
            / "01_simple_crm"
            / "django-angular3.json",
        ):
            with self.subTest(static_config=static_config_path):
                static_config = json.loads(
                    static_config_path.read_text(encoding="utf-8")
                )
                self.assertEqual(
                    static_config["tool"]["ngAddPackage"],
                    "angular-django2@0.4.1",
                )

    def test_project_config_resolves_paths(self) -> None:
        config = load_project_config(
            ROOT / "tests" / "fixtures" / TEST_PROJECT_CONFIG_FILENAME
        )
        self.assertTrue(config.openapi_schema.is_file())
        self.assertTrue(config.openui_specification.is_file())
        self.assertEqual(config.angular_workspace, ROOT / "tmparea" / "angular")
        self.assertEqual(validate_project_config(config), [])

    def test_project_config_loads_separate_project_configuration(self) -> None:
        with tempfile.TemporaryDirectory(dir=WORKSPACE_TEMP_DIR) as tmp:
            root = Path(tmp)
            config_path = root / TEST_PROJECT_CONFIG_FILENAME
            config_path.write_text(
                json.dumps(
                    {
                        "project": {"name": "portal"},
                        "artifacts": {
                            "openapiSchema": "spec/api.json",
                            "openuiSpecification": "spec/app.openui.json",
                            "angularWorkspace": "frontend",
                        },
                    }
                ),
                encoding="utf-8",
            )

            config = load_project_config(config_path)

        self.assertEqual(config.project_name, "portal")
        self.assertEqual(config.openapi_schema, root / "spec" / "api.json")
        self.assertEqual(config.openui_specification, root / "spec" / "app.openui.json")
        self.assertEqual(config.angular_workspace, root / "frontend")
        self.assertFalse(isinstance(config, dict))

    def test_project_config_rejects_unknown_keys(self) -> None:
        with tempfile.TemporaryDirectory(dir=WORKSPACE_TEMP_DIR) as tmp:
            config_path = Path(tmp) / TEST_PROJECT_CONFIG_FILENAME
            config_path.write_text(
                json.dumps(
                    {
                        "project": {"name": "portal", "unsupported": True},
                        "artifacts": {
                            "openapiSchema": "api.json",
                            "openuiSpecification": "app.openui.json",
                            "angularWorkspace": "frontend",
                        },
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ConfigError, "project contains unsupported key\\(s\\): unsupported"
            ):
                load_project_config(config_path)

    def test_project_validation_reports_missing_openui_source(self) -> None:
        with tempfile.TemporaryDirectory(dir=WORKSPACE_TEMP_DIR) as tmp:
            root = Path(tmp)
            openapi_path = root / "api.json"
            openapi_path.write_text(
                json.dumps(valid_openapi_document()),
                encoding="utf-8",
            )
            config_path = root / TEST_PROJECT_CONFIG_FILENAME
            config_path.write_text(
                json.dumps(
                    {
                        "project": {"name": "portal"},
                        "artifacts": {
                            "openapiSchema": "api.json",
                            "openuiSpecification": "missing.openui.json",
                            "angularWorkspace": "frontend",
                        },
                    }
                ),
                encoding="utf-8",
            )

            errors = validate_project_config(load_project_config(config_path))

        self.assertEqual(
            errors,
            ["OpenUI source does not exist: " + str(root / "missing.openui.json")],
        )

    def test_project_validation_reports_invalid_openui_source(self) -> None:
        with tempfile.TemporaryDirectory(dir=WORKSPACE_TEMP_DIR) as tmp:
            root = Path(tmp)
            openapi_path = root / "api.json"
            openapi_path.write_text(
                json.dumps(valid_openapi_document()),
                encoding="utf-8",
            )
            (root / "app.openui.json").write_text(
                json.dumps({"version": "0.0.1", "id": "root", "type": "UnknownType"}),
                encoding="utf-8",
            )
            config_path = root / TEST_PROJECT_CONFIG_FILENAME
            config_path.write_text(
                json.dumps(
                    {
                        "project": {"name": "portal"},
                        "artifacts": {
                            "openapiSchema": "api.json",
                            "openuiSpecification": "app.openui.json",
                            "angularWorkspace": "frontend",
                        },
                    }
                ),
                encoding="utf-8",
            )

            errors = validate_project_config(load_project_config(config_path))

        self.assertEqual(errors, ["unsupported object type: UnknownType"])

    def test_consumer_project_template_uses_project_relative_artifact_paths(
        self,
    ) -> None:
        template_path = (
            ROOT
            / "django_angular3"
            / "templates"
            / "django_angular3"
            / TEST_PROJECT_CONFIG_FILENAME
        )

        config = load_project_config(template_path)

        self.assertEqual(config.project_name, "django-angular3-scaffold")
        self.assertEqual(
            config.openapi_schema,
            template_path.parent / "schema.yaml",
        )
        self.assertEqual(
            config.openui_specification,
            template_path.parent / "spec" / "openui" / "app.openui.json",
        )
        self.assertEqual(
            config.angular_workspace, template_path.parent / "build" / "angular"
        )

    def test_project_config_rejects_legacy_combined_fields(self) -> None:
        with tempfile.TemporaryDirectory(dir=WORKSPACE_TEMP_DIR) as tmp:
            config_path = Path(tmp) / TEST_PROJECT_CONFIG_FILENAME
            config_path.write_text(
                """{
    "project": { "name": "legacy" },
        "openapi": {
            "source": "schema.yaml",
            "ngOpenApiGenConfig": "ng-openapi-gen.json"
        },
    "openui": { "source": "app.openui.json" },
    "angular": { "output": "build/angular" }
}
""",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ConfigError,
                (
                    "Project configuration contains unsupported key\\(s\\): "
                    "angular, openapi, openui"
                ),
            ):
                load_project_config(config_path)

    def test_scenario_matrix_covers_all_change_domains_with_valid_inputs(self) -> None:
        scenarios_root = ROOT / "tests" / "fixtures" / "scenarios"
        matrix = json.loads(
            (scenarios_root / "scenario-matrix.json").read_text(encoding="utf-8")
        )

        expected_domain_combinations = {
            (False, False, False),
            (False, False, True),
            (False, True, False),
            (False, True, True),
            (True, False, False),
            (True, False, True),
            (True, True, False),
            (True, True, True),
        }
        domain_combinations = {
            (
                entry["domains"]["config"],
                entry["domains"]["openapi"],
                entry["domains"]["openui"],
            )
            for entry in matrix
        }

        self.assertEqual(domain_combinations, expected_domain_combinations)
        self.assertEqual(
            {entry["exception"] for entry in matrix if "exception" in entry},
            {"replacement", "source-selection"},
        )
        for entry in matrix:
            with self.subTest(scenario=entry["id"]):
                config_path = _example_project_config_path(scenarios_root / entry["id"])
                self.assertTrue(config_path.is_file())
                self.assertEqual(
                    validate_project_config(load_project_config(config_path)), []
                )

    def test_schema_removal_scenario_removes_customer_email(self) -> None:
        scenario_root = ROOT / "tests" / "fixtures" / "scenarios" / "03-schema-removal"
        candidate = load_project_config(
            scenario_root / "django-angular3-scenario-schema-removal.json"
        )
        baseline = load_project_config(
            scenario_root / "django-angular3-scenario-schema-removal.previous.json"
        )

        self.assertEqual(validate_project_config(candidate), [])
        self.assertEqual(validate_project_config(baseline), [])
        candidate_customer = load_document(candidate.openapi_schema)["components"][
            "schemas"
        ]["Customer"]
        baseline_customer = load_document(baseline.openapi_schema)["components"][
            "schemas"
        ]["Customer"]
        self.assertIn("email", baseline_customer["properties"])
        self.assertIn("email", baseline_customer["required"])
        self.assertNotIn("email", candidate_customer["properties"])
        self.assertNotIn("email", candidate_customer["required"])

    def test_openui_source_scenario_selects_identical_documents(self) -> None:
        scenario_root = ROOT / "tests" / "fixtures" / "scenarios" / "05-openui-source"
        candidate = load_project_config(
            scenario_root / "django-angular3-scenario-openui-source.json"
        )
        baseline = load_project_config(
            scenario_root / "django-angular3-scenario-openui-source.previous.json"
        )

        self.assertNotEqual(
            candidate.openui_specification,
            baseline.openui_specification,
        )
        self.assertEqual(
            load_document(candidate.openui_specification),
            load_document(baseline.openui_specification),
        )

    def test_dashboard_scenario_contains_all_documented_nodes(self) -> None:
        document = load_document(
            ROOT
            / "tests"
            / "fixtures"
            / "scenarios"
            / "shared"
            / "dashboard.openui.json"
        )

        def node_ids(node: object) -> set[str]:
            if not isinstance(node, Mapping):
                return set()
            mapping = cast(Mapping[str, object], node)
            identifier = mapping.get("id")
            identifiers: set[str] = (
                {identifier} if isinstance(identifier, str) else set()
            )
            children = mapping.get("children", ())
            if not isinstance(children, Sequence) or isinstance(children, str):
                return identifiers
            for child in cast(Sequence[object], children):
                identifiers.update(node_ids(child))
            return identifiers

        self.assertEqual(validate_openui_document(document), [])
        self.assertTrue(
            {"dashboardPage", "customerSummary", "productSummary"} <= node_ids(document)
        )

    def test_static_config_scenarios_change_only_workspace_style(self) -> None:
        scenarios_root = ROOT / "tests" / "fixtures" / "scenarios"
        matrix = json.loads(
            (scenarios_root / "scenario-matrix.json").read_text(encoding="utf-8")
        )
        static_scenarios = {
            entry["id"]: entry["staticConfig"]
            for entry in matrix
            if "staticConfig" in entry
        }

        self.assertEqual(
            set(static_scenarios),
            {
                "04-workspace-style",
                "10-config-openapi",
                "11-config-openui",
                "12-all-change-domains",
            },
        )
        for scenario, paths in static_scenarios.items():
            with self.subTest(scenario=scenario):
                baseline = load_document(scenarios_root / paths["baseline"])
                candidate = load_document(scenarios_root / paths["candidate"])
                changes = compare_static_config(
                    baseline,
                    candidate,
                    source=str(scenarios_root / paths["candidate"]),
                )

                self.assertEqual(len(changes), 1)
                self.assertEqual(changes[0].path, "/angular/workspace/style")
                self.assertEqual((changes[0].before, changes[0].after), ("scss", "css"))

    def test_validation_only_generator_fixture_is_not_packaged(self) -> None:
        fixture_path = ARTIFACT_FIXTURES / "ng-openapi-gen" / "ng-openapi-gen.json"
        self.assertTrue(fixture_path.is_file())
        document = json.loads(fixture_path.read_text(encoding="utf-8"))
        self.assertEqual(
            document,
            {
                "$schema": (
                    "https://raw.githubusercontent.com/cyclosproject/ng-openapi-gen/"
                    "master/ng-openapi-gen-schema.json"
                ),
                "input": "../openapi/example.openapi.json",
                "output": "../../../../tmparea/angular/generated/ng-openapi-gen",
                "serviceSuffix": "Api",
                "modelIndex": True,
            },
        )
        self.assertEqual(
            (fixture_path.parent / document["input"]).resolve(),
            ARTIFACT_FIXTURES / "openapi" / "example.openapi.json",
        )

        manifest_text = (ROOT / "MANIFEST.in").read_text(encoding="utf-8")
        package_data_text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertNotIn("tests/fixtures", manifest_text)
        self.assertNotIn('"tests/**/*"', package_data_text)

    def test_pyproject_declares_runtime_dependencies(self) -> None:
        pyproject_path = ROOT / "pyproject.toml"
        self.assertTrue(pyproject_path.is_file())

        pyproject = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
        dependencies = set(pyproject["project"]["dependencies"])

        expected_runtime_dependencies = {
            "Django>=5.1",
            "djangorestframework",
            "django-filter",
            "drf-spectacular",
            "claude-agent-sdk",
            "openui-spec==0.0.2",
            "openapi-spec-validator>=0.7",
        }
        self.assertEqual(dependencies, expected_runtime_dependencies)

    def test_install_tutorial_copies_expected_files(self) -> None:
        with tempfile.TemporaryDirectory(dir=WORKSPACE_TEMP_DIR) as tmp:
            dest = str(Path(tmp) / "simple_crm")
            result = _run_install_tutorial(dest)
            self.assertEqual(result, 0)
            dest_path = Path(dest)
            self.assertTrue((dest_path / "manage.py").is_file())
            self.assertTrue((dest_path / "django-angular3.json").is_file())
            self.assertTrue((dest_path / TUTORIAL_PROJECT_CONFIG_FILENAME).is_file())
            self.assertTrue((dest_path / "app.openui.json").is_file())
            self.assertTrue((dest_path / "simple_crm" / "settings.py").is_file())

    def test_install_tutorial_fails_if_dest_exists(self) -> None:
        with tempfile.TemporaryDirectory(dir=WORKSPACE_TEMP_DIR) as tmp:
            result = _run_install_tutorial(tmp)
            self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
