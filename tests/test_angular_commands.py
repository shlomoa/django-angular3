import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from django_angular3.cli import main


ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "django-angular3.json"

try:
    import django
except ImportError:  # pragma: no cover - exercised when Django is not installed
    DJANGO_AVAILABLE = False
else:
    DJANGO_AVAILABLE = True


class AngularCliCommandTests(unittest.TestCase):
    def run_cli(self, *args: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = main(args)
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def test_ng_new_dry_run_prints_empty_workspace_command(self) -> None:
        exit_code, stdout, stderr = self.run_cli("ng_new", str(CONFIG_PATH), "--dry-run")

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        plan = json.loads(stdout)
        self.assertEqual(
            plan[0]["argv"],
            [
                "ng",
                "new",
                "django-angular3-scaffold",
                "--defaults",
                "--skip-git",
                "--skip-install",
                "--no-create-application",
                "--package-manager=npm",
                f"--directory={ROOT / 'build' / 'angular'}",
            ],
        )

    def test_ng_config_dry_run_prints_workspace_configuration_commands(self) -> None:
        exit_code, stdout, stderr = self.run_cli("ng_config", str(CONFIG_PATH), "--dry-run")

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        plan = json.loads(stdout)
        self.assertEqual(len(plan), 3)
        self.assertEqual(plan[0]["argv"], ["ng", "config", "cli.packageManager", "npm"])
        self.assertEqual(
            plan[1]["argv"],
            ["ng", "config", "schematics.@schematics/angular:application.style", "scss"],
        )
        self.assertEqual(
            plan[2]["argv"],
            ["ng", "config", "schematics.@schematics/angular:application.routing", "true"],
        )

    def test_ng_build_dry_run_prints_project_build_command(self) -> None:
        exit_code, stdout, stderr = self.run_cli("ng_build", str(CONFIG_PATH), "--dry-run")

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        plan = json.loads(stdout)
        self.assertEqual(
            plan[0]["argv"],
            ["ng", "build", "django-angular3-scaffold", "--configuration=production"],
        )

    def test_ng_gen_app_dry_run_supports_app_name_override(self) -> None:
        exit_code, stdout, stderr = self.run_cli(
            "ng_gen_app", str(CONFIG_PATH), "--app-name", "portal", "--dry-run"
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        plan = json.loads(stdout)
        self.assertEqual(
            plan[0]["argv"],
            ["ng", "generate", "application", "portal", "--style=scss", "--routing"],
        )

    def test_ng_openapi_gen_dry_run_uses_openapi_source(self) -> None:
        exit_code, stdout, stderr = self.run_cli("ng_openapi_gen", str(CONFIG_PATH), "--dry-run")

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        plan = json.loads(stdout)
        self.assertEqual(
            plan[0]["argv"],
            [
                "npx",
                "ng-openapi-gen",
                "-i",
                str(ROOT / "spec" / "openapi" / "source" / "example.openapi.json"),
            ],
        )


@unittest.skipUnless(DJANGO_AVAILABLE, "Django is required for management command tests.")
class AngularManagementCommandTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        from django.conf import settings

        if not settings.configured:
            settings.configure(
                SECRET_KEY="test-key",
                USE_TZ=True,
                DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
                INSTALLED_APPS=["django_angular3"],
            )
        django.setup()

    def test_management_commands_support_dry_run(self) -> None:
        cases = (
            ("ng_new", {}),
            ("ng_config", {}),
            ("ng_build", {}),
            ("ng_gen_app", {"app_name": "portal"}),
            ("ng_openapi_gen", {}),
        )

        for command_name, options in cases:
            with self.subTest(command_name=command_name):
                from django.core.management import call_command

                stdout = io.StringIO()
                call_command(command_name, str(CONFIG_PATH), dry_run=True, stdout=stdout, **options)
                self.assertIn('"argv"', stdout.getvalue())
