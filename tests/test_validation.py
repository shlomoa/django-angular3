import json
import tempfile
import unittest
from pathlib import Path

from django_angular3.validation import validate_openui_document, validate_openui_file
from tests.workspace_temp import WORKSPACE_TEMP_DIR


class OpenUiValidationTests(unittest.TestCase):
    def test_accepts_a_valid_openui_document(self) -> None:
        document = {"version": "0.0.1", "id": "root", "type": "Application"}

        self.assertEqual(validate_openui_document(document), [])

    def test_reports_schema_validation_errors_from_openui_spec(self) -> None:
        document = {"version": "not-a-version", "id": "root", "type": "Application"}

        self.assertEqual(
            validate_openui_document(document),
            [
                "$.version: 'not-a-version' does not match "
                "'^[0-9]+\\\\.[0-9]+\\\\.[0-9]+$'"
            ],
        )

    def test_reports_unsupported_catalog_type_from_openui_spec(self) -> None:
        document = {"version": "0.0.1", "id": "root", "type": "UnknownType"}

        self.assertEqual(
            validate_openui_document(document),
            ["unsupported object type: UnknownType"],
        )

    def test_reports_duplicate_ids_from_openui_spec(self) -> None:
        document = {
            "version": "0.0.1",
            "id": "root",
            "type": "Application",
            "children": [
                {"id": "dashboard", "type": "DashboardPage"},
                {"id": "dashboard", "type": "DashboardPage"},
            ],
        }

        self.assertEqual(
            validate_openui_document(document),
            ["duplicate object id: dashboard"],
        )

    def test_reports_document_loading_errors_separately(self) -> None:
        with tempfile.TemporaryDirectory(dir=WORKSPACE_TEMP_DIR) as temporary_directory:
            path = Path(temporary_directory) / "invalid.openui.json"
            path.write_text("{", encoding="utf-8")

            errors = validate_openui_file(path)

        self.assertEqual(len(errors), 1)
        self.assertIn("cannot load JSON document", errors[0])

    def test_validates_openui_files_through_openui_spec(self) -> None:
        document = {"version": "0.0.1", "id": "root", "type": "Application"}
        with tempfile.TemporaryDirectory(dir=WORKSPACE_TEMP_DIR) as temporary_directory:
            path = Path(temporary_directory) / "document.openui.json"
            path.write_text(json.dumps(document), encoding="utf-8")

            self.assertEqual(validate_openui_file(path), [])


if __name__ == "__main__":
    unittest.main()
