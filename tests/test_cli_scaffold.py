import tempfile
import unittest
from pathlib import Path

from django_angular3.cli import _run_install_tutorial
from django_angular3.config import ConfigError, load_project_config
from django_angular3.documents import load_document
from django_angular3.validation import (
    validate_openapi_document,
    validate_openui_document,
    validate_project_config,
)

ROOT = Path(__file__).resolve().parent.parent


class ScaffoldTests(unittest.TestCase):
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
            / "django-angular3.json"
        )
        self.assertEqual(validate_project_config(config), [])

    def test_project_config_resolves_paths(self) -> None:
        config = load_project_config(ROOT / "django-angular3.json")
        self.assertTrue(config.openapi_source.is_file())
        self.assertTrue(config.openui_source.is_file())
        self.assertEqual(config.angular_output, ROOT / "build" / "angular")
        self.assertEqual(validate_project_config(config), [])

    def test_project_config_rejects_legacy_ui_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "django-angular3.json"
            config_path.write_text(
                """{
  "project": { "name": "legacy-ui" },
  "openapi": { "source": "schema.yaml" },
    "ui": { "source": "app.openui.json" },
  "angular": { "output": "build/angular" }
}
""",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ConfigError, "Configuration section 'openui' must be a mapping"
            ):
                load_project_config(config_path)

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
            "openui-spec==0.0.1",
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
        with tempfile.TemporaryDirectory() as tmp:
            dest = str(Path(tmp) / "simple_crm")
            result = _run_install_tutorial(dest)
            self.assertEqual(result, 0)
            dest_path = Path(dest)
            self.assertTrue((dest_path / "manage.py").is_file())
            self.assertTrue((dest_path / "django-angular3.json").is_file())
            self.assertTrue((dest_path / "app.openui.json").is_file())
            self.assertTrue((dest_path / "simple_crm" / "settings.py").is_file())

    def test_install_tutorial_fails_if_dest_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = _run_install_tutorial(tmp)
            self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
