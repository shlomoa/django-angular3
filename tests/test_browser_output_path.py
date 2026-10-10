"""Tests of the mandatory ``angular.build.browserOutputPath`` setting."""

import copy
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch

from django_angular3.angular import (
    _COMMAND_BUILDERS,
    angular_browser_output_dir,
    resolve_angular_command_context,
)
from django_angular3.cli import main
from django_angular3.config import load_project_config
from django_angular3.settings import (
    PACKAGE_DEFAULT_CONFIG_PATH,
    AngularCommandError,
    load_angular_settings,
    validate_tool_configuration,
)
from tests.workspace_temp import WORKSPACE_TEMP_DIR

PROJECT_CONFIG_PATH = (
    Path(__file__).parent / "fixtures" / "django-angular3-project.json"
)
PACKAGED = json.loads(PACKAGE_DEFAULT_CONFIG_PATH.read_text(encoding="utf-8"))


def tool_configuration(**build: object) -> dict[str, object]:
    """The packaged tool configuration with ``angular.build`` replaced by ``build``."""
    document = copy.deepcopy(PACKAGED)
    document["angular"]["build"] = build
    return document


class BrowserOutputPathValidationTests(unittest.TestCase):
    def test_the_packaged_configuration_defines_it(self) -> None:
        self.assertEqual(validate_tool_configuration(PACKAGED), [])
        self.assertIn("browserOutputPath", PACKAGED["angular"]["build"])

    def test_it_is_mandatory(self) -> None:
        errors = validate_tool_configuration(tool_configuration(configuration="x"))

        self.assertIn(
            "angular.build.browserOutputPath must be a non-empty string.", errors
        )

    def test_it_must_stay_inside_the_workspace(self) -> None:
        for value in ("/dist/app/browser", "../dist/app", "dist/../../app", "C:/dist"):
            with self.subTest(value=value):
                errors = validate_tool_configuration(
                    tool_configuration(
                        configuration="production", browserOutputPath=value
                    )
                )
                self.assertIn(
                    "angular.build.browserOutputPath must be a relative path inside "
                    "the workspace.",
                    errors,
                )

    def test_a_relative_directory_is_accepted(self) -> None:
        errors = validate_tool_configuration(
            tool_configuration(
                configuration="production", browserOutputPath="dist/shop/browser"
            )
        )

        self.assertEqual(errors, [])


class BrowserOutputPathLoadingTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(dir=WORKSPACE_TEMP_DIR)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def write_tool_configuration(self, document: dict[str, object]) -> Path:
        path = self.root / "django-angular3.json"
        path.write_text(json.dumps(document), encoding="utf-8")
        return path

    def test_the_configured_value_is_loaded(self) -> None:
        path = self.write_tool_configuration(
            tool_configuration(
                configuration="production", browserOutputPath="out/shop/browser"
            )
        )

        settings = load_angular_settings(config_path=path)

        self.assertEqual(settings.browser_output_path, "out/shop/browser")

    def test_a_configuration_without_it_is_rejected(self) -> None:
        path = self.write_tool_configuration(
            tool_configuration(configuration="production")
        )

        with self.assertRaisesRegex(AngularCommandError, "browserOutputPath"):
            load_angular_settings(config_path=path)

    def test_there_is_no_default_in_code(self) -> None:
        missing = self.root / "absent" / "django-angular3.json"

        with self.assertRaisesRegex(AngularCommandError, "browserOutputPath"):
            load_angular_settings(config_path=missing)

    def test_the_directory_is_the_workspace_plus_the_setting(self) -> None:
        project = load_project_config(PROJECT_CONFIG_PATH)
        path = self.write_tool_configuration(
            tool_configuration(
                configuration="production", browserOutputPath="out/shop/browser"
            )
        )

        directory = angular_browser_output_dir(
            project, load_angular_settings(config_path=path)
        )

        self.assertEqual(directory, project.angular_workspace / "out/shop/browser")


class NgdjCommandsFailWithoutItTests(unittest.TestCase):
    """Every command that runs Angular tooling needs the setting."""

    def setUp(self) -> None:
        discovery = patch(
            "django_angular3.config.discover_project_config_path",
            return_value=PROJECT_CONFIG_PATH,
        )
        discovery.start()
        self.addCleanup(discovery.stop)
        temporary = tempfile.TemporaryDirectory(dir=WORKSPACE_TEMP_DIR)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        previous = Path.cwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, previous)

    def test_every_command_fails_when_the_tool_configuration_lacks_it(self) -> None:
        (self.root / "django-angular3.json").write_text(
            json.dumps(tool_configuration(configuration="production")),
            encoding="utf-8",
        )

        self.assertTrue(_COMMAND_BUILDERS)
        for command in _COMMAND_BUILDERS:
            with self.subTest(command=command):
                with self.assertRaisesRegex(AngularCommandError, "browserOutputPath"):
                    resolve_angular_command_context(command)

    def test_the_command_line_reports_it_and_exits_with_an_error(self) -> None:
        (self.root / "django-angular3.json").write_text(
            json.dumps(tool_configuration(configuration="production")),
            encoding="utf-8",
        )
        stderr = io.StringIO()

        with redirect_stderr(stderr):
            exit_code = main(["ng_build", "--dry-run"])

        self.assertEqual(exit_code, 1)
        self.assertIn("browserOutputPath", stderr.getvalue())

    def test_a_configuration_that_defines_it_resolves_the_command(self) -> None:
        (self.root / "django-angular3.json").write_text(
            json.dumps(
                tool_configuration(
                    configuration="production", browserOutputPath="dist/x/browser"
                )
            ),
            encoding="utf-8",
        )

        _, settings, invocations = resolve_angular_command_context("ng_build")

        self.assertEqual(settings.browser_output_path, "dist/x/browser")
        self.assertTrue(invocations)


if __name__ == "__main__":
    unittest.main()
