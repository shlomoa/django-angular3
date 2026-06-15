import io
import json
import os
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from django_angular3.angular import AngularInvocation, AngularCommandError, execute_invocations
from django_angular3.cli import main
from django_angular3.settings import AngularSettings, DEFAULT_ANGULAR_SETTINGS, load_angular_settings


ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "django-angular3.json"

try:
    import django
except ImportError:  # pragma: no cover - exercised when Django is not installed
    DJANGO_AVAILABLE = False
else:
    DJANGO_AVAILABLE = True
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.test_settings")
    django.setup()


class AngularCliCommandTests(unittest.TestCase):
    def test_load_angular_settings_with_and_without_overrides(self) -> None:
        overridden_settings = DEFAULT_ANGULAR_SETTINGS | {
            "ng_executable": "ng.cmd",
            "package_manager": "npm",
        }

        self.assertEqual(load_angular_settings(), AngularSettings(**DEFAULT_ANGULAR_SETTINGS))
        self.assertEqual(
            load_angular_settings({"ng_executable": "ng.cmd", "package_manager": "npm"}),
            AngularSettings(**overridden_settings),
        )

    def test_load_angular_settings_supports_legacy_package_executable_aliases(self) -> None:
        with_npx_alias = DEFAULT_ANGULAR_SETTINGS | {"pnpm_executable": "corepack-pnpm"}
        with_npm_alias = DEFAULT_ANGULAR_SETTINGS | {"pnpm_executable": "pnpm.cmd"}

        self.assertEqual(
            load_angular_settings({"npx_executable": "corepack-pnpm"}),
            AngularSettings(**with_npx_alias),
        )
        self.assertEqual(
            load_angular_settings({"npm_executable": "pnpm.cmd"}),
            AngularSettings(**with_npm_alias),
        )

    def test_load_angular_settings_normalizes_command_allowlist(self) -> None:
        settings = load_angular_settings(
            {"command_allowlist": ["NG_OPENAPI_GEN", " ng_openapi_gen "]}
        )

        self.assertEqual(settings.command_allowlist, ("ng_openapi_gen",))

    def run_cli(self, *args: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = main(args)
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def test_ng_new_dry_run_prints_empty_workspace_command(self) -> None:
        exit_code, stdout, stderr = self.run_cli("ng_new", str(CONFIG_PATH), "--dry-run")

        ng = DEFAULT_ANGULAR_SETTINGS["ng_executable"]
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        plan = json.loads(stdout)
        # ng new runs from angular_output.parent so --directory is just the final component
        self.assertEqual(
            plan[0]["argv"],
            [
                ng,
                "new",
                "django-angular3-scaffold",
                "--defaults",
                "--skip-git",
                "--skip-install",
                "--no-create-application",
                "--package-manager=pnpm",
                "--directory=angular",
            ],
        )

    def test_ng_workspace_dry_run_bootstraps_workspace_with_ngdj_schematic(self) -> None:
        exit_code, stdout, stderr = self.run_cli("ng_workspace", str(CONFIG_PATH), "--dry-run")

        ng = DEFAULT_ANGULAR_SETTINGS["ng_executable"]
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        plan = json.loads(stdout)
        self.assertEqual(len(plan), 6)
        self.assertEqual(
            plan[0]["argv"],
            [
                ng,
                "new",
                "django-angular3-scaffold",
                "--defaults",
                "--skip-git",
                "--skip-install",
                "--no-create-application",
                "--package-manager=pnpm",
                "--directory=angular",
            ],
        )
        self.assertEqual(
            plan[-1]["argv"],
            [ng, "generate", "angular-django2:ng-workspace", "django-angular3-scaffold"],
        )

    def test_ng_config_dry_run_prints_workspace_configuration_commands(self) -> None:
        exit_code, stdout, stderr = self.run_cli("ng_config", str(CONFIG_PATH), "--dry-run")

        ng = DEFAULT_ANGULAR_SETTINGS["ng_executable"]
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        plan = json.loads(stdout)
        self.assertEqual(len(plan), 3)
        self.assertEqual(plan[0]["argv"], [ng, "config", "cli.packageManager", "pnpm"])
        self.assertEqual(
            plan[1]["argv"],
            [ng, "config", "schematics.@schematics/angular:application.style", "scss"],
        )
        self.assertEqual(
            plan[2]["argv"],
            [ng, "config", "schematics.@schematics/angular:application.routing", "true"],
        )

    def test_ng_build_dry_run_prints_project_build_command(self) -> None:
        exit_code, stdout, stderr = self.run_cli("ng_build", str(CONFIG_PATH), "--dry-run")

        ng = DEFAULT_ANGULAR_SETTINGS["ng_executable"]
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        plan = json.loads(stdout)
        self.assertEqual(
            plan[0]["argv"],
            [ng, "build", "django-angular3-scaffold", "--configuration=production"],
        )

    def test_ng_gen_app_dry_run_supports_app_name_override(self) -> None:
        exit_code, stdout, stderr = self.run_cli(
            "ng_gen_app", str(CONFIG_PATH), "--app-name", "portal", "--dry-run"
        )

        ng = DEFAULT_ANGULAR_SETTINGS["ng_executable"]
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        plan = json.loads(stdout)
        self.assertEqual(
            plan[0]["argv"],
            [ng, "generate", "angular-django2:ng-app", "portal", "--style=scss", "--routing"],
        )

    def test_ng_openapi_gen_dry_run_uses_openapi_source(self) -> None:
        exit_code, stdout, stderr = self.run_cli("ng_openapi_gen", str(CONFIG_PATH), "--dry-run")

        pnpm = DEFAULT_ANGULAR_SETTINGS["pnpm_executable"]
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        plan = json.loads(stdout)
        self.assertEqual(
            plan[0]["argv"],
            [
                pnpm,
                "exec",
                "ng-openapi-gen",
                "-i",
                str(ROOT / "spec" / "openapi" / "source" / "example.openapi.json"),
            ],
        )

    def test_ng_add_dry_run_defaults_to_angular_django2(self) -> None:
        exit_code, stdout, stderr = self.run_cli("ng_add", str(CONFIG_PATH), "--dry-run")

        ng = DEFAULT_ANGULAR_SETTINGS["ng_executable"]
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        plan = json.loads(stdout)
        self.assertEqual(
            plan[0]["argv"],
            [ng, "add", "angular-django2", "--skip-confirmation"],
        )

    def test_ng_add_dry_run_accepts_custom_package(self) -> None:
        exit_code, stdout, stderr = self.run_cli(
            "ng_add", str(CONFIG_PATH), "--package", "@angular/material", "--dry-run"
        )

        ng = DEFAULT_ANGULAR_SETTINGS["ng_executable"]
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        plan = json.loads(stdout)
        self.assertEqual(
            plan[0]["argv"],
            [ng, "add", "@angular/material", "--skip-confirmation"],
        )

    def test_execute_invocations_rejects_commands_outside_allowlist(self) -> None:
        settings = load_angular_settings()
        invocation = AngularInvocation(
            command_name="ng_build",
            argv=("pnpm", "exec", "ng-openapi-gen"),
            cwd=ROOT,
        )

        with patch("django_angular3.angular.subprocess.run") as run:
            with self.assertRaisesRegex(
                AngularCommandError,
                r"Command 'ng_build' is not allowed\. Allowed commands: ng_openapi_gen\.",
            ):
                execute_invocations([invocation], settings)

        run.assert_not_called()

    def test_execute_invocations_allows_whitelisted_commands(self) -> None:
        settings = load_angular_settings({"command_allowlist": ["ng_openapi_gen"]})
        invocation = AngularInvocation(
            command_name="ng_openapi_gen",
            argv=("pnpm", "exec", "ng-openapi-gen"),
            cwd=ROOT,
        )

        with patch("django_angular3.angular.subprocess.run") as run:
            execute_invocations([invocation], settings)

        run.assert_called_once_with(invocation.argv, cwd=invocation.cwd, check=True)


@unittest.skipUnless(DJANGO_AVAILABLE, "Django is required for management command tests.")
class AngularManagementCommandTests(unittest.TestCase):
    def test_management_commands_support_dry_run(self) -> None:
        cases = (
            ("ng_new", {}),
            ("ng_workspace", {}),
            ("ng_config", {}),
            ("ng_build", {}),
            ("ng_gen_app", {"app_name": "portal"}),
            ("ng_openapi_gen", {}),
            ("ng_add", {}),
        )

        for command_name, options in cases:
            with self.subTest(command_name=command_name):
                from django.core.management import call_command

                stdout = io.StringIO()
                call_command(command_name, str(CONFIG_PATH), dry_run=True, stdout=stdout, **options)
                self.assertIn('"argv"', stdout.getvalue())
