from pathlib import Path
import shutil
import unittest

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
        document = load_document(ROOT / "spec" / "openapi" / "source" / "example.openapi.json")
        self.assertEqual(validate_openapi_document(document), [])

    def test_example_ui_document_is_valid(self) -> None:
        document = load_document(ROOT / "spec" / "ui" / "example.ui.json")
        self.assertEqual(validate_ui_document(document), [])

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


if __name__ == "__main__":
    unittest.main()
