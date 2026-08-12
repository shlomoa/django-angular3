import io
import json
import tempfile
import unittest
import warnings
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from django_angular3.cli import main
from tests.workspace_temp import WORKSPACE_TEMP_DIR

TEST_CONFIG_FILENAME = "project.json"


class ValidationCliTests(unittest.TestCase):
    def run_cli(self, *args: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            warnings.catch_warnings(),
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            warnings.simplefilter("ignore", UserWarning)
            exit_code = main(args)
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def test_validate_openui_accepts_valid_document(self) -> None:
        with tempfile.TemporaryDirectory(dir=WORKSPACE_TEMP_DIR) as tmp:
            path = Path(tmp) / "app.openui.json"
            path.write_text(
                json.dumps({"version": "0.0.1", "id": "root", "type": "Application"}),
                encoding="utf-8",
            )

            exit_code, stdout, stderr = self.run_cli("validate-openui", str(path))

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertIn(f"UI document {path} is valid.", stdout)

    def test_validate_openui_reports_invalid_document_path(self) -> None:
        with tempfile.TemporaryDirectory(dir=WORKSPACE_TEMP_DIR) as tmp:
            path = Path(tmp) / "invalid.openui.json"
            path.write_text(
                json.dumps({"version": "0.0.1", "id": "root", "type": "UnknownType"}),
                encoding="utf-8",
            )

            exit_code, stdout, stderr = self.run_cli("validate-openui", str(path))

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout, "")
        self.assertIn(f"UI document {path} is invalid.", stderr)
        self.assertIn("unsupported object type: UnknownType", stderr)

    def test_validate_project_accepts_valid_configured_openui_document(self) -> None:
        with tempfile.TemporaryDirectory(dir=WORKSPACE_TEMP_DIR) as tmp:
            root = Path(tmp)
            (root / "api.json").write_text(
                json.dumps({"openapi": "3.0.3", "paths": {"/items/": {"get": {}}}}),
                encoding="utf-8",
            )
            (root / "app.openui.json").write_text(
                json.dumps({"version": "0.0.1", "id": "root", "type": "Application"}),
                encoding="utf-8",
            )
            config_path = root / TEST_CONFIG_FILENAME
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
            with patch(
                "django_angular3.config.discover_project_config_path",
                return_value=config_path,
            ):
                exit_code, stdout, stderr = self.run_cli("validate-project")

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertIn("Project configuration", stdout)
        self.assertIn("is valid.", stdout)

    def test_validate_project_reports_invalid_configured_openui_document(self) -> None:
        with tempfile.TemporaryDirectory(dir=WORKSPACE_TEMP_DIR) as tmp:
            root = Path(tmp)
            (root / "api.json").write_text(
                json.dumps({"openapi": "3.0.3", "paths": {"/items/": {"get": {}}}}),
                encoding="utf-8",
            )
            (root / "app.openui.json").write_text(
                json.dumps({"version": "0.0.1", "id": "root", "type": "UnknownType"}),
                encoding="utf-8",
            )
            config_path = root / TEST_CONFIG_FILENAME
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
            with patch(
                "django_angular3.config.discover_project_config_path",
                return_value=config_path,
            ):
                exit_code, stdout, stderr = self.run_cli("validate-project")

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout, "")
        self.assertIn("Project configuration", stderr)
        self.assertIn("unsupported object type: UnknownType", stderr)


if __name__ == "__main__":
    unittest.main()
