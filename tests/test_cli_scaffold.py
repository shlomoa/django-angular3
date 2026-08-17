import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from django_angular3.cli import _run_install_tutorial
from django_angular3.config import (
    ConfigError,
    discover_project_config_path,
    load_project_config,
    project_config_path,
)
from django_angular3.documents import load_document
from django_angular3.validation import (
    validate_openapi_document,
    validate_openui_document,
    validate_project_config,
)
from tests.openapi_fixtures import valid_openapi_document
from tests.workspace_temp import WORKSPACE_TEMP_DIR

ROOT = Path(__file__).resolve().parent.parent
TEST_PROJECT_CONFIG_FILENAME = "django-angular3-project.json"
TUTORIAL_PROJECT_CONFIG_FILENAME = "django-angular3-simple_crm.json"


def _example_project_config_path(example_directory: Path) -> Path:
    config_paths = [
        path
        for path in example_directory.glob("django-angular3-*.json")
        if path.name != "django-angular3.json"
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
        document = load_document(
            ROOT / "spec" / "openapi" / "source" / "example.openapi.json"
        )
        self.assertEqual(validate_openapi_document(document), [])

    def test_example_openui_document_is_valid(self) -> None:
        document = load_document(ROOT / "spec" / "openui" / "app.openui.json")
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

    def test_consumer_project_template_uses_canonical_schema(self) -> None:
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
            template_path.parent
            / "spec"
            / "openapi"
            / "source"
            / "example.openapi.json",
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
        examples_root = ROOT / "spec" / "examples"
        matrix = json.loads(
            (examples_root / "scenario-matrix.json").read_text(encoding="utf-8")
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
                config_path = _example_project_config_path(examples_root / entry["id"])
                self.assertTrue(config_path.is_file())
                self.assertEqual(
                    validate_project_config(load_project_config(config_path)), []
                )

    def test_validation_only_generator_fixture_is_not_packaged(self) -> None:
        fixture_path = (
            ROOT / "spec" / "openapi" / "ng-openapi-gen" / "ng-openapi-gen.json"
        )
        self.assertTrue(fixture_path.is_file())

        manifest_text = (ROOT / "MANIFEST.in").read_text(encoding="utf-8")
        package_data_text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertNotIn("spec/openapi", manifest_text)
        self.assertNotIn('"spec/**/*"', package_data_text)

    def test_requirements_file_exists_with_runtime_dependencies(self) -> None:
        requirements_path = ROOT / "requirements.txt"
        self.assertTrue(requirements_path.is_file())

        requirements_lines = [
            line.strip()
            for line in requirements_path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]

        expected_runtime_dependencies = {
            "Django>=5.1",
            "djangorestframework",
            "django-filter",
            "drf-spectacular",
            "openui-spec==0.0.2",
        }
        self.assertEqual(set(requirements_lines), expected_runtime_dependencies)

    def test_manifest_includes_requirements_file(self) -> None:
        manifest_path = ROOT / "MANIFEST.in"
        self.assertTrue(manifest_path.is_file())

        manifest_lines = {
            line.strip()
            for line in manifest_path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        self.assertIn("include requirements.txt", manifest_lines)

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
