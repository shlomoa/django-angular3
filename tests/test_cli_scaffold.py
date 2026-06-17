import shutil
import unittest
from pathlib import Path

from django_angular3.build import create_build_plan, write_build_plan
from django_angular3.config import load_project_config
from django_angular3.documents import load_document
from django_angular3.validation import (
    validate_openapi_document,
    validate_project_config,
    validate_ui_document,
)

ROOT = Path(__file__).resolve().parent.parent


class ScaffoldTests(unittest.TestCase):
    def test_example_openapi_document_is_valid(self) -> None:
        document = load_document(
            ROOT / "spec" / "openapi" / "source" / "example.openapi.json"
        )
        self.assertEqual(validate_openapi_document(document), [])

    def test_example_ui_document_is_valid(self) -> None:
        document = load_document(ROOT / "spec" / "ui" / "example.ui.json")
        self.assertEqual(validate_ui_document(document), [])

    def test_tutorial_ui_document_is_valid(self) -> None:
        document = load_document(
            ROOT / "django_angular3" / "examples" / "01_simple_crm" / "ui.json"
        )
        self.assertEqual(validate_ui_document(document), [])

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
        self.assertTrue(config.ui_source.is_file())
        self.assertEqual(config.angular_output, ROOT / "build" / "angular")
        self.assertEqual(validate_project_config(config), [])

    def test_build_plan_can_be_written(self) -> None:
        config = load_project_config(ROOT / "django-angular3.json")
        plan = create_build_plan(config)
        output_dir = ROOT / ".test-build-plan"
        if output_dir.exists():
            shutil.rmtree(output_dir)

        try:
            plan_path = write_build_plan(plan, output_dir)
            self.assertTrue(plan_path.is_file())
            self.assertIn("plan.json", str(plan_path))
        finally:
            if output_dir.exists():
                shutil.rmtree(output_dir)

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


if __name__ == "__main__":
    unittest.main()
