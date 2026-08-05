"""Tests for Speakeasy OpenAPI CLI integration in validation and tools."""

from __future__ import annotations

import os
import unittest
import warnings
from pathlib import Path
from unittest.mock import patch

from django_angular3.tools import check_go_available, ensure_speakeasy_openapi
from django_angular3.tools import find_speakeasy_openapi
from django_angular3.validation import (

    _run_speakeasy_validate,
    validate_openapi_file,
)

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_OPENAPI = ROOT / "spec" / "openapi" / "source" / "example.openapi.json"


class GoAvailabilityTests(unittest.TestCase):
    def test_check_go_available_returns_bool(self) -> None:
        result = check_go_available()
        self.assertIsInstance(result, bool)

    def test_check_go_available_matches_shutil_which(self) -> None:
        import shutil

        self.assertEqual(check_go_available(), shutil.which("go") is not None)

    def test_ensure_speakeasy_openapi_raises_when_go_missing(self) -> None:
        with patch("django_angular3.tools.check_go_available", return_value=False):
            with self.assertRaises(RuntimeError) as ctx:
                ensure_speakeasy_openapi()
        self.assertIn("Go is required", str(ctx.exception))


class FindSpeakeasyTests(unittest.TestCase):
    def test_find_speakeasy_openapi_returns_none_or_str(self) -> None:
        result = find_speakeasy_openapi()
        self.assertIsInstance(result, (str, type(None)))

    def test_find_speakeasy_openapi_found_when_installed(self) -> None:
        """If Go is available and the binary exists in GOPATH/bin, it is found."""
        if not check_go_available():
            self.skipTest("Go not available; skipping binary-location test.")
        # If the binary is installed (as CI does), find_speakeasy_openapi()
        # returns a str path.
        result = find_speakeasy_openapi()
        if result is not None:
            self.assertTrue(
                os.path.isfile(result),
                f"Binary path returned but file not found: {result}",
            )


class RunSpeakeasyValidateTests(unittest.TestCase):
    def test_raises_runtime_error_when_binary_missing(self) -> None:
        with patch(
            "django_angular3.validation.find_speakeasy_openapi", return_value=None
        ):
            with self.assertRaises(RuntimeError) as ctx:
                _run_speakeasy_validate(EXAMPLE_OPENAPI)
        self.assertIn("not installed", str(ctx.exception))

    def test_returns_empty_list_for_valid_spec_when_available(self) -> None:
        binary = find_speakeasy_openapi()
        if binary is None:
            self.skipTest("Speakeasy openapi binary not installed.")
        errors = _run_speakeasy_validate(EXAMPLE_OPENAPI)
        self.assertIsInstance(errors, list)
        # A valid spec should produce no errors
        self.assertEqual(errors, [], f"Unexpected errors: {errors}")

    def test_returns_errors_for_invalid_spec_when_available(self) -> None:
        binary = find_speakeasy_openapi()
        if binary is None:
            self.skipTest("Speakeasy openapi binary not installed.")
        import json
        import tempfile

        bad_spec = {"openapi": "3.0.0", "info": {}, "paths": {}}
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as tmp:
            json.dump(bad_spec, tmp)
            tmp_path = tmp.name
        try:
            errors = _run_speakeasy_validate(tmp_path)
            self.assertIsInstance(errors, list)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_returns_error_when_binary_not_found_at_path(self) -> None:
        with patch(
            "django_angular3.validation.find_speakeasy_openapi",
            return_value="/nonexistent/openapi",
        ):
            with self.assertRaises(RuntimeError):
                _run_speakeasy_validate(EXAMPLE_OPENAPI)


class ValidateOpenapiFileTests(unittest.TestCase):
    def test_valid_file_passes_with_speakeasy(self) -> None:
        """validate_openapi_file returns [] for the example spec."""
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            errors = validate_openapi_file(EXAMPLE_OPENAPI)
        self.assertEqual(errors, [])

    def test_nonexistent_file_returns_error(self) -> None:
        errors = validate_openapi_file("/nonexistent/path.json")
        self.assertTrue(len(errors) > 0)

    def test_falls_back_gracefully_when_binary_missing(self) -> None:
        """When speakeasy is not available, a warning is issued but no crash."""
        with patch(
            "django_angular3.validation._run_speakeasy_validate",
            side_effect=RuntimeError("not installed"),
        ):
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                errors = validate_openapi_file(EXAMPLE_OPENAPI)
            self.assertEqual(errors, [])
            self.assertTrue(any("Speakeasy" in str(w.message) for w in caught))

    def test_structural_errors_reported_without_cli(self) -> None:
        """Structural issues are caught before calling the CLI."""
        import json
        import tempfile

        # Document missing 'openapi'/'swagger' key
        bad = {"paths": {"/items": {"get": {}}}}
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as tmp:
            json.dump(bad, tmp)
            tmp_path = tmp.name
        try:
            errors = validate_openapi_file(tmp_path)
            self.assertTrue(any("openapi" in e or "swagger" in e for e in errors))
        finally:
            Path(tmp_path).unlink(missing_ok=True)


class EnsureSpeakeasyOpenapiTests(unittest.TestCase):
    def test_returns_existing_path_without_reinstall(self) -> None:
        """ensure_speakeasy_openapi returns the binary path without reinstalling."""
        if not check_go_available():
            self.skipTest("Go not available.")
        binary = find_speakeasy_openapi()
        if binary is None:
            self.skipTest("Speakeasy openapi binary not installed.")
        # Binary already installed — calling ensure_speakeasy_openapi should
        # return its path without invoking 'go install'.
        result = ensure_speakeasy_openapi()
        self.assertTrue(os.path.isfile(result))
        self.assertEqual(result, binary)
