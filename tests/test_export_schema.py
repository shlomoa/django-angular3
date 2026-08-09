"""Tests for the export_schema management command and versioning helpers."""

from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import django
from django.test import override_settings

from django_angular3.config import get_previous_schema_path, load_project_config
from django_angular3.management.commands.build_app import _command_for_skill
from tests.workspace_temp import WORKSPACE_TEMP_DIR

ROOT = Path(__file__).resolve().parent.parent

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.test_settings")
django.setup()


# ---------------------------------------------------------------------------
# Unit tests for the versioning path helper
# ---------------------------------------------------------------------------


class GetPreviousSchemaPathTests(unittest.TestCase):
    def test_json_extension(self) -> None:
        source = Path("/project/spec/openapi/source/api.json")
        expected = Path("/project/spec/openapi/source/api.previous.json")
        self.assertEqual(get_previous_schema_path(source), expected)

    def test_yaml_extension(self) -> None:
        source = Path("/project/spec/openapi/source/api.yaml")
        expected = Path("/project/spec/openapi/source/api.previous.yaml")
        self.assertEqual(get_previous_schema_path(source), expected)

    def test_multi_dot_stem(self) -> None:
        source = Path("/project/spec/openapi/source/example.openapi.json")
        expected = Path("/project/spec/openapi/source/example.openapi.previous.json")
        self.assertEqual(get_previous_schema_path(source), expected)

    def test_derived_from_project_config(self) -> None:
        config = load_project_config(
            ROOT / "tests" / "fixtures" / "django-angular3-project.json"
        )
        previous = get_previous_schema_path(config.openapi_schema)
        # Previous must live in the same directory as the source.
        self.assertEqual(previous.parent, config.openapi_schema.parent)
        # Previous file name must contain ".previous".
        self.assertIn(".previous", previous.name)
        # Previous file must have the same suffix as the source.
        self.assertEqual(previous.suffix, config.openapi_schema.suffix)


# ---------------------------------------------------------------------------
# Management command tests (require Django)
# ---------------------------------------------------------------------------


class ExportSchemaCommandTests(unittest.TestCase):
    """Tests for the export_schema management command."""

    CONFIG_PATH = str(ROOT / "tests" / "fixtures" / "django-angular3-project.json")

    def setUp(self) -> None:
        self.base_dir = override_settings(BASE_DIR=Path(self.CONFIG_PATH).parent)
        self.base_dir.enable()
        self.addCleanup(self.base_dir.disable)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _make_schema_bytes(self) -> bytes:
        """Return minimal valid OpenAPI schema bytes (JSON)."""
        schema = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/items/": {"get": {"responses": {"200": {"description": "ok"}}}}
            },
        }
        return json.dumps(schema, indent=2).encode()

    def _mock_spectacular(self, schema_bytes: bytes):
        """Patch the direct drf-spectacular command and write its output."""

        def write_schema(command_name: str, **options: object) -> None:
            from django.conf import settings as django_settings

            self.assertEqual(command_name, "spectacular")
            self.spectacular_settings_during_export = dict(
                django_settings.SPECTACULAR_SETTINGS
            )
            Path(str(options["file"])).write_bytes(schema_bytes)

        return patch(
            "django_angular3.management.commands.export_schema.call_command",
            side_effect=write_schema,
        )

    # ------------------------------------------------------------------
    # Dry-run
    # ------------------------------------------------------------------

    def test_dry_run_prints_destination_and_no_files_written(self) -> None:
        from django.core.management import call_command

        stdout = io.StringIO()
        # dry-run does not invoke drf-spectacular, so no mock is needed.
        call_command(
            "export_schema",
            dry_run=True,
            stdout=stdout,
        )

        output = stdout.getvalue()
        self.assertIn("DRY RUN", output)
        self.assertIn("destination", output)
        self.assertIn("no files written", output)

    def test_dry_run_does_not_create_any_files(self) -> None:
        """dry-run must never write schema or previous-schema files."""
        from django.core.management import call_command

        config = load_project_config(self.CONFIG_PATH)
        destination = config.openapi_schema
        previous_path = get_previous_schema_path(destination)

        # Record which files exist before the run.
        existed_before = destination.exists()
        previous_existed_before = previous_path.exists()

        # dry-run does not invoke drf-spectacular, so no mock is needed.
        call_command("export_schema", dry_run=True)

        # Neither file state should have changed.
        self.assertEqual(destination.exists(), existed_before)
        self.assertEqual(previous_path.exists(), previous_existed_before)

    # ------------------------------------------------------------------
    # Normal write flow
    # ------------------------------------------------------------------

    def test_writes_schema_to_configured_destination(self) -> None:
        from django.core.management import call_command

        config = load_project_config(self.CONFIG_PATH)
        destination = config.openapi_schema
        previous_path = get_previous_schema_path(destination)

        # Keep originals to restore after the test.
        original_content = destination.read_bytes() if destination.exists() else None
        previous_existed_before = previous_path.exists()
        from django.conf import settings as django_settings

        had_original_settings = hasattr(django_settings, "SPECTACULAR_SETTINGS")
        original_settings = getattr(django_settings, "SPECTACULAR_SETTINGS", None)

        schema_bytes = self._make_schema_bytes()

        try:
            with self._mock_spectacular(schema_bytes) as mock_spectacular:
                stdout = io.StringIO()
                call_command("export_schema", stdout=stdout)

            mock_spectacular.assert_called_once()
            self.assertEqual(
                mock_spectacular.call_args.kwargs["format"], "openapi-json"
            )
            self.assertEqual(
                mock_spectacular.call_args.kwargs["file"], str(destination)
            )
            self.assertEqual(
                self.spectacular_settings_during_export,
                {
                    "TITLE": "Example API",
                    "VERSION": "1.0.0",
                    "SERVE_INCLUDE_SCHEMA": False,
                },
            )
            self.assertEqual(
                hasattr(django_settings, "SPECTACULAR_SETTINGS"),
                had_original_settings,
            )
            if had_original_settings:
                self.assertEqual(
                    django_settings.SPECTACULAR_SETTINGS, original_settings
                )

            # New schema must exist at the configured path.
            self.assertTrue(destination.exists())
            self.assertEqual(destination.read_bytes(), schema_bytes)

            output = stdout.getvalue()
            self.assertIn(str(destination), output)
        finally:
            # Restore original state.
            if previous_path.exists() and not previous_existed_before:
                previous_path.unlink()
            if original_content is not None:
                destination.write_bytes(original_content)
            elif destination.exists():
                destination.unlink()

    def test_rotates_existing_schema_to_previous(self) -> None:
        """When a current schema exists, it should be renamed to .previous."""
        from django.core.management import call_command

        config = load_project_config(self.CONFIG_PATH)
        destination = config.openapi_schema
        previous_path = get_previous_schema_path(destination)

        original_content = destination.read_bytes() if destination.exists() else None

        # Ensure a previous file does not block the test.
        if previous_path.exists():
            previous_path.unlink()

        schema_bytes = self._make_schema_bytes()

        try:
            with self._mock_spectacular(schema_bytes):
                stdout = io.StringIO()
                call_command("export_schema", stdout=stdout)

            # The previous schema must now exist and contain the old content.
            if original_content is not None:
                self.assertTrue(previous_path.exists())
                self.assertEqual(previous_path.read_bytes(), original_content)

            output = stdout.getvalue()
            if original_content is not None:
                self.assertIn("archived", output)
        finally:
            if previous_path.exists():
                previous_path.unlink()
            if original_content is not None:
                destination.write_bytes(original_content)
            elif destination.exists():
                destination.unlink()

    # ------------------------------------------------------------------
    # build_app auto-discovery
    # ------------------------------------------------------------------

    @unittest.skip("build_app command is a work in progress")
    def test_build_app_auto_detects_previous_schema(self) -> None:
        """build_app should auto-discover the .previous schema
        written by export_schema."""
        from django.core.management import call_command

        config = load_project_config(self.CONFIG_PATH)
        previous_path = get_previous_schema_path(config.openapi_schema)

        # Write a minimal previous schema next to the current one.
        minimal_schema = {
            "openapi": "3.0.0",
            "info": {"title": "prev", "version": "0.9.0"},
            "paths": {
                "/items/": {"get": {"responses": {"200": {"description": "ok"}}}}
            },
        }
        previous_path.write_text(json.dumps(minimal_schema), encoding="utf-8")

        try:
            stdout = io.StringIO()
            # Mock oasdiff so we don't need the binary installed in CI.
            with (
                patch(
                    "django_angular3.management.commands.build_app.ensure_oasdiff",
                    return_value="oasdiff",
                ),
                patch(
                    "django_angular3.management.commands.build_app.subprocess.run"
                ) as mock_run,
            ):
                # oasdiff diff returns empty (no changes).
                mock_run.return_value = MagicMock(stdout="{}", stderr="", returncode=0)
                call_command(
                    "build_app",
                    self.CONFIG_PATH,
                    dry_run=True,
                    stdout=stdout,
                )

            output = stdout.getvalue()
            self.assertIn("Auto-detected previous schema", output)
        finally:
            if previous_path.exists():
                previous_path.unlink()

    @unittest.skip("build_app command is a work in progress")
    def test_build_app_validates_project_sources_before_change_detection(self) -> None:
        from django.core.management import call_command
        from django.core.management.base import CommandError

        with tempfile.TemporaryDirectory(dir=WORKSPACE_TEMP_DIR) as directory:
            project_root = Path(directory)
            openapi_path = project_root / "openapi.json"
            openapi_path.write_text(
                json.dumps(
                    {
                        "openapi": "3.0.0",
                        "paths": {
                            "/items/": {
                                "get": {"responses": {"200": {"description": "ok"}}}
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            config_path = project_root / "django-angular3.json"
            config_path.write_text(
                json.dumps(
                    {
                        "project": {"name": "invalid-ui"},
                        "openapi": {"source": "openapi.json"},
                        "openui": {"source": "missing.openui.json"},
                        "angular": {"output": "build/angular"},
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(CommandError, "OpenUI source does not exist"):
                call_command("build_app", str(config_path), dry_run=True)

    def test_build_app_uses_ng_workspace_command_for_workspace_setup_create_steps(
        self,
    ) -> None:
        self.assertEqual(
            _command_for_skill("workspace-setup", "create"), "ng_workspace"
        )
        self.assertEqual(_command_for_skill("material-app", "create"), "ng_gen_app")
        self.assertEqual(
            _command_for_skill("openapi-setup", "create"), "ng_openapi_gen"
        )
        self.assertEqual(
            _command_for_skill("openapi-setup", "modify"), "ng_openapi_gen"
        )
        self.assertEqual(
            _command_for_skill("angular-workspace-foundation", "create"),
            "ng_workspace",
        )
        self.assertEqual(
            _command_for_skill("angular-app-composition", "create"),
            "ng_gen_app",
        )
        self.assertEqual(
            _command_for_skill("angular-api-integration", "create"),
            "ng_openapi_gen",
        )


if __name__ == "__main__":
    unittest.main()
