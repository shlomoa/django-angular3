"""Tests that the tool configuration is mandatory, discovered like the project one.

``django-angular3.json`` has no fallback: it is found next to the project configuration
(``settings.BASE_DIR`` in a configured Django runtime, else the current directory) and
a project without one is an error, not the packaged example.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import PropertyMock, patch

import django
from django.conf import settings as django_settings
from django.test import override_settings

from django_angular3.angular import _COMMAND_BUILDERS, resolve_angular_command_context
from django_angular3.settings import (
    TOOL_CONFIG_TEMPLATE_PATH,
    AngularCommandError,
    discover_tool_config_path,
    load_angular_settings,
    load_drf_spectacular_settings,
    load_ng_openapi_gen_settings,
    validate_tool_configuration,
)
from tests.workspace_temp import WORKSPACE_TEMP_DIR

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.test_settings")
django.setup()

TEMPLATE = json.loads(TOOL_CONFIG_TEMPLATE_PATH.read_text(encoding="utf-8"))
PROJECT_CONFIG = Path(__file__).parent / "fixtures" / "django-angular3-project.json"


class ToolConfigurationDiscoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(dir=WORKSPACE_TEMP_DIR)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()

    def test_it_is_found_in_base_dir_in_a_configured_django_runtime(self) -> None:
        with override_settings(BASE_DIR=self.root):
            self.assertEqual(
                discover_tool_config_path(), self.root / "django-angular3.json"
            )

    def test_it_is_found_in_the_current_directory_otherwise(self) -> None:
        previous = Path.cwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, previous)
        # A BASE_DIR that must be ignored when Django is not configured.
        ignored = self.root / "ignored"
        not_configured = patch.object(
            type(django_settings),
            "configured",
            new_callable=PropertyMock,
            return_value=False,
        )

        with override_settings(BASE_DIR=ignored), not_configured:
            self.assertEqual(
                discover_tool_config_path(), self.root / "django-angular3.json"
            )

    def test_the_packaged_template_is_not_a_fallback(self) -> None:
        with override_settings(BASE_DIR=self.root):
            with self.assertRaises(AngularCommandError) as raised:
                load_angular_settings()

        message = str(raised.exception)
        self.assertIn(str(self.root / "django-angular3.json"), message)
        self.assertIn("mandatory", message)
        # The remedy names where to start from.
        self.assertIn(str(TOOL_CONFIG_TEMPLATE_PATH), message)

    def test_every_loader_fails_without_the_file(self) -> None:
        loaders = (
            load_angular_settings,
            load_ng_openapi_gen_settings,
            load_drf_spectacular_settings,
        )
        with override_settings(BASE_DIR=self.root):
            for loader in loaders:
                with self.subTest(loader=loader.__name__):
                    with self.assertRaisesRegex(AngularCommandError, "mandatory"):
                        loader()

    def test_an_explicit_path_that_does_not_exist_is_an_error_too(self) -> None:
        missing = self.root / "elsewhere" / "django-angular3.json"

        with self.assertRaisesRegex(AngularCommandError, "elsewhere"):
            load_angular_settings(config_path=missing)

    def test_every_command_fails_without_the_file(self) -> None:
        self.assertTrue(_COMMAND_BUILDERS)
        with (
            override_settings(BASE_DIR=self.root),
            patch(
                "django_angular3.config.discover_project_config_path",
                return_value=PROJECT_CONFIG,
            ),
        ):
            for command in _COMMAND_BUILDERS:
                with self.subTest(command=command):
                    with self.assertRaisesRegex(AngularCommandError, "mandatory"):
                        resolve_angular_command_context(command)

    def test_the_file_next_to_the_project_is_used(self) -> None:
        (self.root / "django-angular3.json").write_text(
            json.dumps(TEMPLATE), encoding="utf-8"
        )

        with override_settings(BASE_DIR=self.root):
            settings = load_angular_settings()

        self.assertEqual(settings.config_path, str(self.root / "django-angular3.json"))
        self.assertEqual(
            settings.browser_output_path,
            TEMPLATE["angular"]["build"]["browserOutputPath"],
        )


class NgAddPackageIsMandatoryTests(unittest.TestCase):
    """The ngdj pin is project configuration; there is no default for it either."""

    def test_the_pin_is_required(self) -> None:
        document = json.loads(json.dumps(TEMPLATE))
        del document["tool"]["ngAddPackage"]

        errors = validate_tool_configuration(document)

        self.assertIn("tool.ngAddPackage must be a non-empty string.", errors)


if __name__ == "__main__":
    unittest.main()
