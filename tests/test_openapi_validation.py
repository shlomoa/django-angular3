"""Tests for openapi-spec-validator based OpenAPI validation."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from django_angular3.validation import validate_openapi_file
from tests.workspace_temp import WORKSPACE_TEMP_DIR

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_OPENAPI = ROOT / "spec" / "openapi" / "source" / "example.openapi.json"


class ValidateOpenapiFileTests(unittest.TestCase):
    def test_valid_file_passes(self) -> None:
        """validate_openapi_file returns [] for the example spec."""
        errors = validate_openapi_file(EXAMPLE_OPENAPI)
        self.assertEqual(errors, [])

    def test_nonexistent_file_returns_error(self) -> None:
        errors = validate_openapi_file("/nonexistent/path.json")
        self.assertTrue(len(errors) > 0)

    def test_structural_errors_reported_before_spec_validation(self) -> None:
        """Structural issues are caught before running full spec validation."""
        # Document missing 'openapi'/'swagger' key.
        bad = {"paths": {"/items": {"get": {}}}}
        tmp_path = self._write_temp(bad)
        try:
            errors = validate_openapi_file(tmp_path)
            self.assertTrue(any("openapi" in e or "swagger" in e for e in errors))
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_spec_validation_reports_oas_violation(self) -> None:
        """A structurally-plausible but OAS-invalid document is rejected."""
        # Path parameter '{id}' is referenced but never declared, which passes
        # the lightweight structural check but violates the OpenAPI spec.
        bad = {
            "openapi": "3.0.3",
            "info": {"title": "Bad API", "version": "0.1.0"},
            "paths": {
                "/items/{id}/": {
                    "get": {
                        "operationId": "getItem",
                        "responses": {"200": {"description": "ok"}},
                    }
                }
            },
        }
        tmp_path = self._write_temp(bad)
        try:
            errors = validate_openapi_file(tmp_path)
            self.assertTrue(len(errors) > 0)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    @staticmethod
    def _write_temp(document: dict) -> str:
        with tempfile.NamedTemporaryFile(
            suffix=".json", mode="w", delete=False, dir=WORKSPACE_TEMP_DIR
        ) as tmp:
            json.dump(document, tmp)
            return tmp.name


if __name__ == "__main__":
    unittest.main()
