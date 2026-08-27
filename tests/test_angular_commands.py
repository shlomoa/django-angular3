import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

import django
from django.core.management.base import CommandError
from django.test import override_settings

from django_angular3.angular import (
    AngularCommandError,
    AngularInvocation,
    execute_invocations,
)
from django_angular3.cli import build_parser, main
from django_angular3.config import (
    discover_project_config_path,
    project_config_path,
)
from django_angular3.management.commands.ng_build import Command as NgBuildCommand
from django_angular3.settings import (
    DjangoAngularSettings,
    load_angular_settings,
    load_drf_spectacular_settings,
    load_ng_openapi_gen_settings,
    validate_ng_openapi_gen_configuration,
    validate_tool_configuration,
)
from tests.workspace_temp import WORKSPACE_TEMP_DIR

ROOT = Path(__file__).resolve().parent.parent
PROJECT_CONFIG_PATH = ROOT / "tests" / "fixtures" / "django-angular3-project.json"
EXAMPLE_OPENAPI = (
    ROOT / "tests" / "fixtures" / "artifacts" / "openapi" / "example.openapi.json"
)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.test_settings")
django.setup()


class AngularCliCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.project_config_discovery = patch(
            "django_angular3.config.discover_project_config_path",
            return_value=PROJECT_CONFIG_PATH,
        )
        self.project_config_discovery.start()
        self.addCleanup(self.project_config_discovery.stop)

    def test_django_project_config_discovery_uses_base_directory(self) -> None:
        with tempfile.TemporaryDirectory(dir=WORKSPACE_TEMP_DIR) as tmp:
            project_root = Path(tmp)
            with override_settings(BASE_DIR=project_root):
                self.assertEqual(
                    discover_project_config_path(),
                    project_root / project_config_path(),
                )

    def test_load_angular_settings_from_static_tool_configuration(self) -> None:
        settings = load_angular_settings()
        self.assertEqual(settings.package_manager, "pnpm")
        self.assertEqual(settings.style, "scss")
        self.assertTrue(settings.routing)
        self.assertFalse(settings.ssr)
        self.assertTrue(settings.zoneless)
        self.assertEqual(settings.build_configuration, "production")
        self.assertEqual(settings.ng_add_package, "angular-django2@0.4.1")

    def test_load_angular_settings_applies_explicit_overrides(self) -> None:
        overridden_settings = load_angular_settings().__dict__ | {
            "ng_executable": "ng.cmd",
            "package_manager": "npm",
        }
        self.assertEqual(
            load_angular_settings(
                {"ng_executable": "ng.cmd", "package_manager": "npm"}
            ),
            DjangoAngularSettings(**overridden_settings),
        )

    def test_load_angular_settings_normalizes_command_allowlist(self) -> None:
        settings = load_angular_settings(
            {"command_allowlist": ["NG_OPENAPI_GEN", " ng_openapi_gen "]}
        )

        self.assertEqual(settings.command_allowlist, ("ng_openapi_gen",))

    def test_loads_global_generator_settings_from_tool_configuration(self) -> None:
        with tempfile.TemporaryDirectory(dir=WORKSPACE_TEMP_DIR) as temporary_directory:
            config_path = Path(temporary_directory) / "django-angular3.json"
            config_path.write_text(
                json.dumps(
                    {
                        "ngOpenApiGen": {
                            "serviceSuffix": "Client",
                            "modelIndex": True,
                        },
                        "drfSpectacular": {
                            "settings": {"TITLE": "Portal API", "VERSION": "2.0"}
                        },
                        "oasdiff": {"format": "json"},
                    }
                ),
                encoding="utf-8",
            )

            self.assertEqual(
                load_ng_openapi_gen_settings(config_path),
                {"serviceSuffix": "Client", "modelIndex": True},
            )
            self.assertEqual(
                load_drf_spectacular_settings(config_path),
                {"TITLE": "Portal API", "VERSION": "2.0"},
            )

    def test_global_generator_configuration_rejects_invalid_values(self) -> None:
        errors = validate_ng_openapi_gen_configuration(
            {"ngOpenApiGen": {"serviceSuffix": "", "modelIndex": "yes"}}
        )

        self.assertIn("ngOpenApiGen.serviceSuffix must be a non-empty string.", errors)
        self.assertIn("ngOpenApiGen.modelIndex must be a boolean.", errors)

    def test_global_generator_configuration_rejects_per_run_values(self) -> None:
        errors = validate_ng_openapi_gen_configuration(
            {
                "ngOpenApiGen": {
                    "serviceSuffix": "Client",
                    "modelIndex": True,
                    "$schema": "https://example.test/schema.json",
                    "input": "schema.yaml",
                    "output": "generated/api",
                }
            }
        )

        self.assertIn(
            "ngOpenApiGen must not define per-run setting(s): $schema, input, output.",
            errors,
        )

    def test_validate_tool_configuration_rejects_missing_required_clauses(self) -> None:
        errors = validate_tool_configuration({"angular": {}})
        self.assertIn("ngOpenApiGen must be a mapping.", errors)
        self.assertIn("drfSpectacular must be a mapping.", errors)
        self.assertIn("tool must be a mapping.", errors)

    def run_cli(self, *args: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = main(args)
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def test_cli_project_commands_reject_configuration_path_arguments(self) -> None:
        parser = build_parser()

        with self.assertRaises(SystemExit):
            parser.parse_args(["ng_build", str(PROJECT_CONFIG_PATH)])

        with self.assertRaises(SystemExit):
            parser.parse_args(["validate-project", str(PROJECT_CONFIG_PATH)])

    def test_cli_project_command_help_has_no_path_parameter(self) -> None:
        help_text = (
            build_parser()
            ._subparsers._group_actions[0]
            .choices["ng_build"]
            .format_help()
        )

        self.assertNotIn("[path]", help_text)
        self.assertNotIn("project config", help_text.lower())

    def test_ng_new_dry_run_prints_empty_workspace_command(self) -> None:
        exit_code, stdout, stderr = self.run_cli("ng_new", "--dry-run")

        ng = load_angular_settings().ng_executable
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        plan = json.loads(stdout)
        self.assertEqual(plan["projectConfig"], str(PROJECT_CONFIG_PATH))
        self.assertEqual(plan["toolConfig"], "django-angular3.json")
        # ng new runs from angular_workspace.parent, so --directory is
        # just the final component.
        self.assertEqual(
            plan["invocations"][0]["argv"],
            [
                ng,
                "new",
                "django-angular3-test",
                "--defaults",
                "--skip-git",
                "--skip-install",
                "--no-create-application",
                "--package-manager=pnpm",
                "--directory=angular",
            ],
        )

    def test_ng_workspace_dry_run_bootstraps_workspace_with_ngdj_schematic(
        self,
    ) -> None:
        exit_code, stdout, stderr = self.run_cli("ng_workspace", "--dry-run")

        ng = load_angular_settings().ng_executable
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        plan = json.loads(stdout)
        self.assertEqual(len(plan["invocations"]), 6)
        self.assertEqual(
            plan["invocations"][0]["argv"],
            [
                ng,
                "new",
                "django-angular3-test",
                "--defaults",
                "--skip-git",
                "--skip-install",
                "--no-create-application",
                "--package-manager=pnpm",
                "--directory=angular",
            ],
        )
        self.assertEqual(
            plan["invocations"][-1]["argv"],
            [
                ng,
                "generate",
                "angular-django2:workspace-setup",
                "django-angular3-test",
            ],
        )

    def test_ng_config_dry_run_prints_workspace_configuration_commands(self) -> None:
        exit_code, stdout, stderr = self.run_cli("ng_config", "--dry-run")

        ng = load_angular_settings().ng_executable
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        plan = json.loads(stdout)
        self.assertEqual(len(plan["invocations"]), 3)
        self.assertEqual(
            plan["invocations"][0]["argv"],
            [ng, "config", "cli.packageManager", "pnpm"],
        )
        self.assertEqual(
            plan["invocations"][1]["argv"],
            [ng, "config", "schematics.@schematics/angular:application.style", "scss"],
        )
        self.assertEqual(
            plan["invocations"][2]["argv"],
            [
                ng,
                "config",
                "schematics.@schematics/angular:application.routing",
                "true",
            ],
        )

    def test_ng_build_dry_run_prints_project_build_command(self) -> None:
        exit_code, stdout, stderr = self.run_cli("ng_build", "--dry-run")

        ng = load_angular_settings().ng_executable
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        plan = json.loads(stdout)
        self.assertEqual(
            plan["invocations"][0]["argv"],
            [ng, "build", "django-angular3-test", "--configuration=production"],
        )

    def test_ng_gen_app_dry_run_supports_app_name_override(self) -> None:
        exit_code, stdout, stderr = self.run_cli(
            "ng_gen_app", "--app-name", "portal", "--dry-run"
        )

        ng = load_angular_settings().ng_executable
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        plan = json.loads(stdout)
        self.assertEqual(
            plan["invocations"][0]["argv"],
            [
                ng,
                "generate",
                "angular-django2:material-app",
                "portal",
                "--style=scss",
                "--routing",
                "--ssr=false",
                "--zoneless=true",
                "--defaults",
            ],
        )

    def test_ng_gen_app_flags_follow_ssr_and_zoneless_settings(self) -> None:
        from django_angular3.angular import build_ng_gen_app_invocations
        from django_angular3.config import load_project_config

        config = load_project_config(PROJECT_CONFIG_PATH)
        overridden = DjangoAngularSettings(
            **(load_angular_settings().__dict__ | {"ssr": True, "zoneless": False})
        )

        invocations = build_ng_gen_app_invocations(config, overridden)

        argv = invocations[0].argv
        self.assertIn("--ssr=true", argv)
        self.assertIn("--zoneless=false", argv)
        self.assertIn("--defaults", argv)

    def test_ng_complex_component_dry_run_resolves_ngdj_schematic(self) -> None:
        exit_code, stdout, stderr = self.run_cli(
            "ng_complex_component",
            "--name",
            "dashboard-card",
            "--target-path",
            "src/app/features/dashboard",
            "--features",
            "mixins,nested,projection,cdk-overlay",
            "--project",
            "portal",
            "--dry-run",
        )

        ng = load_angular_settings().ng_executable
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        plan = json.loads(stdout)
        self.assertEqual(
            plan["invocations"][0]["argv"],
            [
                ng,
                "generate",
                "angular-django2:complex-component",
                "dashboard-card",
                "--path=src/app/features/dashboard",
                "--features=mixins,nested,projection,cdk-overlay",
                "--mode=create",
                "--project=portal",
            ],
        )

    def test_ng_complex_component_delete_requires_confirmation(self) -> None:
        exit_code, _stdout, stderr = self.run_cli(
            "ng_complex_component",
            "--name",
            "dashboard-card",
            "--target-path",
            "src/app/features/dashboard",
            "--features",
            "nested",
            "--mode",
            "delete",
            "--dry-run",
        )

        self.assertEqual(exit_code, 1)
        self.assertIn("Complex component deletion requires --confirm.", stderr)

    def test_ng_complex_component_rejects_invalid_options(self) -> None:
        exit_code, _stdout, stderr = self.run_cli(
            "ng_complex_component",
            "--name",
            "DashboardCard",
            "--target-path",
            "../outside",
            "--features",
            "unknown",
            "--dry-run",
        )

        self.assertEqual(exit_code, 1)
        self.assertIn("Complex component name must be kebab-case.", stderr)

    def test_ng_page_dry_run_resolves_ngdj_schematic(self) -> None:
        exit_code, stdout, stderr = self.run_cli(
            "ng_page",
            "--name",
            "orders",
            "--target-path",
            "src/app/features/orders",
            "--project",
            "portal",
            "--route-path",
            "sales/orders",
            "--access",
            "protected",
            "--auth-guard",
            "portalGuard",
            "--navigation-label",
            "Orders",
            "--navigation-icon",
            "shopping_cart",
            "--dry-run",
        )

        ng = load_angular_settings().ng_executable
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(
            json.loads(stdout)["invocations"][0]["argv"],
            [
                ng,
                "generate",
                "angular-django2:page",
                "orders",
                "--path=src/app/features/orders",
                "--access=protected",
                "--project=portal",
                "--routePath=sales/orders",
                "--authGuard=portalGuard",
                "--navigationLabel=Orders",
                "--navigationIcon=shopping_cart",
            ],
        )

    def test_ng_page_rejects_non_kebab_case_name(self) -> None:
        exit_code, _stdout, stderr = self.run_cli(
            "ng_page",
            "--name",
            "OrdersPage",
            "--target-path",
            "src/app/features/orders",
            "--dry-run",
        )

        self.assertEqual(exit_code, 1)
        self.assertIn("Page name must be kebab-case.", stderr)

    def test_ng_component_dry_run_resolves_ngdj_schematic(self) -> None:
        exit_code, stdout, stderr = self.run_cli(
            "ng_component",
            "--name",
            "order-card",
            "--target-path",
            "src/app/shared",
            "--project",
            "portal",
            "--dry-run",
        )

        ng = load_angular_settings().ng_executable
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(
            json.loads(stdout)["invocations"][0]["argv"],
            [
                ng,
                "generate",
                "angular-django2:component",
                "order-card",
                "--path=src/app/shared",
                "--project=portal",
            ],
        )

    def test_ng_component_rejects_path_outside_workspace(self) -> None:
        exit_code, _stdout, stderr = self.run_cli(
            "ng_component",
            "--name",
            "order-card",
            "--target-path",
            "../outside",
            "--dry-run",
        )

        self.assertEqual(exit_code, 1)
        self.assertIn("Component target path must be a non-empty relative path", stderr)

    def test_ng_reactive_form_dry_run_resolves_ngdj_schematic(self) -> None:
        exit_code, stdout, stderr = self.run_cli(
            "ng_reactive_form",
            "--name",
            "contact",
            "--definition",
            "forms/contact.json",
            "--target-path",
            "src/app/features/contact",
            "--project",
            "portal",
            "--primitives-path",
            "src/app/shared/form-helpers",
            "--dry-run",
        )

        ng = load_angular_settings().ng_executable
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(
            json.loads(stdout)["invocations"][0]["argv"],
            [
                ng,
                "generate",
                "angular-django2:reactive-form",
                "contact",
                "--definition=forms/contact.json",
                "--path=src/app/features/contact",
                "--project=portal",
                "--primitivesPath=src/app/shared/form-helpers",
            ],
        )

    def test_ng_reactive_form_rejects_definition_outside_workspace(self) -> None:
        exit_code, _stdout, stderr = self.run_cli(
            "ng_reactive_form",
            "--name",
            "contact",
            "--definition",
            "../contact.json",
            "--dry-run",
        )

        self.assertEqual(exit_code, 1)
        self.assertIn(
            "Reactive form definition must be a non-empty relative path", stderr
        )

    def test_ng_site_dry_run_resolves_ngdj_schematic(self) -> None:
        exit_code, stdout, stderr = self.run_cli(
            "ng_site",
            "--source",
            "app.openui.json",
            "--project",
            "portal",
            "--operation",
            "modify",
            "--auth-guard",
            "portalGuard",
            "--csrf-cookie-name",
            "portalcsrftoken",
            "--csrf-header-name",
            "X-Portal-CSRFToken",
            "--dry-run",
        )

        ng = load_angular_settings().ng_executable
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(
            json.loads(stdout)["invocations"][0]["argv"],
            [
                ng,
                "generate",
                "angular-django2:site",
                "--operation=modify",
                "--authGuard=portalGuard",
                "--csrfCookieName=portalcsrftoken",
                "--csrfHeaderName=X-Portal-CSRFToken",
                "--source=app.openui.json",
                "--project=portal",
            ],
        )

    def test_ng_site_create_requires_source_or_defaults(self) -> None:
        exit_code, _stdout, stderr = self.run_cli("ng_site", "--dry-run")

        self.assertEqual(exit_code, 1)
        self.assertIn("Site requires exactly one of --source or --defaults.", stderr)

    def test_ng_site_delete_requires_confirmation(self) -> None:
        exit_code, _stdout, stderr = self.run_cli(
            "ng_site",
            "--operation",
            "delete",
            "--dry-run",
        )

        self.assertEqual(exit_code, 1)
        self.assertIn("Site deletion requires --confirm-delete.", stderr)

    def test_ng_site_delete_uses_manifest_without_source(self) -> None:
        exit_code, stdout, stderr = self.run_cli(
            "ng_site",
            "--operation",
            "delete",
            "--confirm-delete",
            "--dry-run",
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        argv = json.loads(stdout)["invocations"][0]["argv"]
        self.assertIn("--operation=delete", argv)
        self.assertIn("--confirmDelete=true", argv)
        self.assertFalse(any(value.startswith("--source=") for value in argv))
        self.assertNotIn("--defaults=true", argv)

    def test_ng_openapi_gen_dry_run_uses_derived_configuration_file(self) -> None:
        exit_code, stdout, stderr = self.run_cli("ng_openapi_gen", "--dry-run")

        pnpm = load_angular_settings().pnpm_executable
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        plan = json.loads(stdout)
        self.assertEqual(
            plan["invocations"][0]["argv"],
            [
                pnpm,
                "exec",
                "ng-openapi-gen",
                "-c",
                str(ROOT / "tmparea" / "angular" / "ng-openapi-gen.json"),
            ],
        )
        generated_config = ROOT / "tmparea" / "angular" / "ng-openapi-gen.json"
        document = json.loads(generated_config.read_text(encoding="utf-8"))
        self.assertEqual(
            document["$schema"],
            "https://raw.githubusercontent.com/cyclosproject/ng-openapi-gen/"
            "master/ng-openapi-gen-schema.json",
        )
        self.assertEqual(document["serviceSuffix"], "Api")
        self.assertTrue(document["modelIndex"])
        self.assertEqual(
            document["input"],
            str(EXAMPLE_OPENAPI),
        )
        self.assertEqual(
            document["output"],
            str(ROOT / "tmparea" / "angular" / "generated" / "ng-openapi-gen"),
        )
        generated_config.unlink()

    def test_ng_openapi_setup_dry_run_resolves_openapi_setup_schematic(self) -> None:
        exit_code, stdout, stderr = self.run_cli("ng_openapi_setup", "--dry-run")

        ng = load_angular_settings().ng_executable
        schema_path = EXAMPLE_OPENAPI
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        plan = json.loads(stdout)
        self.assertEqual(
            plan["invocations"][0]["argv"],
            [
                ng,
                "generate",
                "angular-django2:openapi-setup",
                f"--openapi_spec_file={schema_path}",
                "--outputPath=src/app/api",
            ],
        )

    def test_ng_openapi_setup_dry_run_appends_helper_and_skip_flags(self) -> None:
        exit_code, stdout, stderr = self.run_cli(
            "ng_openapi_setup",
            "--helpers-path",
            "src/app/api-integration",
            "--skip-helpers",
            "--skip-tests",
            "--dry-run",
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        argv = json.loads(stdout)["invocations"][0]["argv"]
        self.assertIn("--helpersPath=src/app/api-integration", argv)
        self.assertIn("--skipHelpers=true", argv)
        self.assertIn("--skipTests=true", argv)

    def test_ng_data_service_dry_run_resolves_data_service_schematic(self) -> None:
        exit_code, stdout, stderr = self.run_cli(
            "ng_data_service", "--resource", "orders", "--dry-run"
        )

        ng = load_angular_settings().ng_executable
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        plan = json.loads(stdout)
        self.assertEqual(
            plan["invocations"][0]["argv"],
            [
                ng,
                "generate",
                "angular-django2:data-service",
                "orders",
                "--project=django-angular3-test",
            ],
        )

    def test_ng_material_setup_dry_run_defaults_to_project_name(self) -> None:
        exit_code, stdout, stderr = self.run_cli("ng_material_setup", "--dry-run")

        ng = load_angular_settings().ng_executable
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        plan = json.loads(stdout)
        self.assertEqual(
            plan["invocations"][0]["argv"],
            [
                ng,
                "generate",
                "angular-django2:material-setup",
                "--project=django-angular3-test",
            ],
        )

    def test_ng_material_setup_dry_run_appends_material_options(self) -> None:
        exit_code, stdout, stderr = self.run_cli(
            "ng_material_setup",
            "--project",
            "portal",
            "--theme",
            "purple-green",
            "--typography",
            "--no-animations",
            "--dry-run",
        )

        ng = load_angular_settings().ng_executable
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        plan = json.loads(stdout)
        self.assertEqual(
            plan["invocations"][0]["argv"],
            [
                ng,
                "generate",
                "angular-django2:material-setup",
                "--project=portal",
                "--theme=purple-green",
                "--typography=true",
                "--animations=false",
            ],
        )

    def test_ng_add_dry_run_defaults_to_angular_django2(self) -> None:
        exit_code, stdout, stderr = self.run_cli("ng_add", "--dry-run")

        ng = load_angular_settings().ng_executable
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        plan = json.loads(stdout)
        self.assertEqual(
            plan["invocations"][0]["argv"],
            [ng, "add", "angular-django2@0.4.1", "--skip-confirmation"],
        )

    def test_ng_add_dry_run_accepts_custom_package(self) -> None:
        exit_code, stdout, stderr = self.run_cli(
            "ng_add",
            "--package",
            "@angular/material",
            "--dry-run",
        )

        ng = load_angular_settings().ng_executable
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        plan = json.loads(stdout)
        self.assertEqual(
            plan["invocations"][0]["argv"],
            [ng, "add", "@angular/material", "--skip-confirmation"],
        )

    def test_execute_invocations_rejects_commands_outside_allowlist(self) -> None:
        settings = load_angular_settings({"command_allowlist": ["ng_openapi_gen"]})
        invocation = AngularInvocation(
            command_name="ng_build",
            argv=("pnpm", "exec", "ng-openapi-gen"),
            cwd=ROOT,
        )

        with patch("django_angular3.tools.execute_command") as execute_command:
            with self.assertRaisesRegex(
                AngularCommandError,
                (
                    r"Command 'ng_build' is not allowed\. Allowed commands: "
                    r"ng_openapi_gen\."
                ),
            ):
                execute_invocations([invocation], settings)

            execute_command.assert_not_called()

    def test_execute_invocations_allows_whitelisted_commands(self) -> None:
        settings = load_angular_settings({"command_allowlist": ["ng_openapi_gen"]})
        invocation = AngularInvocation(
            command_name="ng_openapi_gen",
            argv=("pnpm", "exec", "ng-openapi-gen"),
            cwd=ROOT,
        )

        with patch("django_angular3.tools.execute_command") as execute_command:
            execute_invocations([invocation], settings)

        execute_command.assert_called_once_with(invocation.argv, cwd=invocation.cwd)


class AngularManagementCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.project_config_discovery = patch(
            "django_angular3.config.discover_project_config_path",
            return_value=PROJECT_CONFIG_PATH,
        )
        self.project_config_discovery.start()
        self.addCleanup(self.project_config_discovery.stop)

    def test_management_command_rejects_configuration_path_arguments(self) -> None:
        parser = NgBuildCommand().create_parser("django-admin", "ng_build")
        with self.assertRaisesRegex(CommandError, "unrecognized arguments"):
            parser.parse_args([str(PROJECT_CONFIG_PATH)])

        self.assertNotIn("project config", parser.format_help().lower())

    def test_validate_project_management_command_accepts_bundled_tutorial(
        self,
    ) -> None:
        from django.core.management import call_command

        tutorial_config = (
            ROOT
            / "django_angular3"
            / "examples"
            / "01_simple_crm"
            / "django-angular3-simple_crm.json"
        )
        stdout = io.StringIO()
        with patch(
            "django_angular3.config.discover_project_config_path",
            return_value=tutorial_config,
        ):
            call_command("validate_project", stdout=stdout)

        self.assertIn("Project configuration is valid.", stdout.getvalue())

    def test_management_commands_support_dry_run(self) -> None:
        cases = (
            ("ng_new", {}),
            ("ng_workspace", {}),
            ("ng_config", {}),
            ("ng_build", {}),
            ("ng_gen_app", {"app_name": "portal"}),
            (
                "ng_complex_component",
                {
                    "name": "dashboard-card",
                    "target_path": "src/app/features/dashboard",
                    "features": "nested",
                },
            ),
            (
                "ng_page",
                {"name": "orders", "target_path": "src/app/features/orders"},
            ),
            ("ng_component", {"name": "order-card"}),
            (
                "ng_reactive_form",
                {"name": "contact", "definition": "forms/contact.json"},
            ),
            ("ng_site", {"defaults": True}),
            ("ng_openapi_gen", {}),
            ("ng_add", {}),
        )

        for command_name, options in cases:
            with self.subTest(command_name=command_name):
                from django.core.management import call_command

                stdout = io.StringIO()
                call_command(
                    command_name,
                    dry_run=True,
                    stdout=stdout,
                    **options,
                )
                plan = json.loads(stdout.getvalue())
                self.assertEqual(plan["projectConfig"], str(PROJECT_CONFIG_PATH))
                self.assertIn("argv", plan["invocations"][0])
