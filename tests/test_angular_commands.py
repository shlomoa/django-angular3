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
    AngularInvocation,
    build_ngdj_schematic_invocations,
)
from django_angular3.cli import build_parser, main
from django_angular3.config import (
    discover_project_config_path,
    load_project_config,
    project_config_path,
)
from django_angular3.management.commands.ng_build import Command as NgBuildCommand
from django_angular3.settings import (
    DEFAULT_NG_ADD_PACKAGE,
    AngularCommandError,
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
        self.assertEqual(settings.ng_add_package, DEFAULT_NG_ADD_PACKAGE)

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

        settings = load_angular_settings()
        ng = settings.ng_executable
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        plan = json.loads(stdout)
        self.assertEqual(plan["projectConfig"], str(PROJECT_CONFIG_PATH))
        self.assertEqual(plan["toolConfig"], settings.config_path)
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
                "--route-path=sales/orders",
                "--auth-guard=portalGuard",
                "--navigation-label=Orders",
                "--navigation-icon=shopping_cart",
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
                "--primitives-path=src/app/shared/form-helpers",
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

    DOCUMENT_ARGS = ("--document", "src/app/app.openui.json")
    NODE_ARGS = ("--node-id", "root")
    DOCUMENT_COMMANDS = {
        "ng_gen_app": (),
        "ng_complex_component": (
            "--name",
            "dashboard-card",
            "--target-path",
            "src/app/features/dashboard",
            "--features",
            "nested",
        ),
        "ng_page": ("--name", "orders", "--target-path", "src/app/features/orders"),
        "ng_component": ("--name", "order-card"),
        "ng_reactive_form": ("--name", "contact"),
    }

    def dry_run_argvs(self, command: str, *args: str) -> list[list[str]]:
        exit_code, stdout, stderr = self.run_cli(command, *args, "--dry-run")
        self.assertEqual((exit_code, stderr), (0, ""))
        return [item["argv"] for item in json.loads(stdout)["invocations"]]

    def test_openui_document_and_node_id_are_forwarded_by_each_wrapper(self) -> None:
        for command, required in self.DOCUMENT_COMMANDS.items():
            with self.subTest(command=command):
                (argv,) = self.dry_run_argvs(
                    command, *required, *self.DOCUMENT_ARGS, *self.NODE_ARGS
                )

                self.assertIn("--document=src/app/app.openui.json", argv)
                self.assertIn("--node-id=root", argv)
                self.assertNotIn("--definition", " ".join(argv))

    def test_ng_workspace_forwards_the_document_to_workspace_setup(self) -> None:
        argvs = self.dry_run_argvs("ng_workspace", *self.DOCUMENT_ARGS)

        setup = argvs[-1]
        self.assertIn("angular-django2:workspace-setup", setup)
        self.assertIn("--document=src/app/app.openui.json", setup)
        self.assertEqual(
            sum("--document=src/app/app.openui.json" in argv for argv in argvs), 1
        )

    def test_invocations_without_a_document_carry_no_document_flags(self) -> None:
        for command, required in self.DOCUMENT_COMMANDS.items():
            with self.subTest(command=command):
                args = (
                    ("--definition", "forms/contact.json")
                    if command == "ng_reactive_form"
                    else ()
                )
                (argv,) = self.dry_run_argvs(command, *required, *args)

                self.assertFalse(
                    [arg for arg in argv if arg.startswith(("--document", "--node-id"))]
                )

    def test_a_node_id_requires_a_document(self) -> None:
        for command, required in self.DOCUMENT_COMMANDS.items():
            with self.subTest(command=command):
                exit_code, _stdout, stderr = self.run_cli(
                    command, *required, *self.NODE_ARGS, "--dry-run"
                )

                self.assertEqual(exit_code, 1)
                self.assertIn("node id requires a document", stderr)

    def test_a_document_must_stay_inside_the_workspace(self) -> None:
        for command, required in self.DOCUMENT_COMMANDS.items():
            with self.subTest(command=command):
                exit_code, _stdout, stderr = self.run_cli(
                    command, *required, "--document", "../outside.json", "--dry-run"
                )

                self.assertEqual(exit_code, 1)
                self.assertIn("document must be a non-empty relative path", stderr)

    def test_a_blank_node_id_is_rejected(self) -> None:
        exit_code, _stdout, stderr = self.run_cli(
            "ng_page",
            *self.DOCUMENT_COMMANDS["ng_page"],
            *self.DOCUMENT_ARGS,
            "--node-id",
            " ",
            "--dry-run",
        )

        self.assertEqual(exit_code, 1)
        self.assertIn("node id must not be empty", stderr)

    def test_reactive_form_needs_exactly_one_of_document_and_definition(self) -> None:
        for extra in (
            (),
            (*self.DOCUMENT_ARGS, "--definition", "forms/contact.json"),
        ):
            with self.subTest(extra=extra):
                exit_code, _stdout, stderr = self.run_cli(
                    "ng_reactive_form", "--name", "contact", *extra, "--dry-run"
                )

                self.assertEqual(exit_code, 1)
                self.assertIn("exactly one of a document or a definition", stderr)

    def test_complex_component_document_requires_create_mode(self) -> None:
        exit_code, _stdout, stderr = self.run_cli(
            "ng_complex_component",
            *self.DOCUMENT_COMMANDS["ng_complex_component"],
            *self.DOCUMENT_ARGS,
            "--mode",
            "modify",
            "--dry-run",
        )

        self.assertEqual(exit_code, 1)
        self.assertIn("document requires mode create", stderr)

    def test_flags_the_openui_node_describes_are_left_out_with_a_document(self) -> None:
        """ngdj rejects ``--access``, ``--routing`` and ``--features`` next to
        ``--document``, so the wrappers' defaults must not emit them."""
        (page,) = self.dry_run_argvs(
            "ng_page",
            *self.DOCUMENT_COMMANDS["ng_page"],
            *self.DOCUMENT_ARGS,
        )
        (app,) = self.dry_run_argvs("ng_gen_app", *self.DOCUMENT_ARGS)

        self.assertFalse([arg for arg in page if arg.startswith("--access")])
        self.assertNotIn("--routing", app)
        self.assertNotIn("--no-routing", app)

    def test_the_same_flags_are_kept_without_a_document(self) -> None:
        (page,) = self.dry_run_argvs("ng_page", *self.DOCUMENT_COMMANDS["ng_page"])
        (app,) = self.dry_run_argvs("ng_gen_app")

        self.assertIn("--access=public", page)
        self.assertIn("--routing", app)

    def test_complex_component_features_are_optional_only_with_a_document(self) -> None:
        from django_angular3.angular import build_ng_complex_component_invocations
        from django_angular3.config import load_project_config
        from django_angular3.settings import AngularCommandError, load_angular_settings

        config = load_project_config(PROJECT_CONFIG_PATH)
        settings = load_angular_settings()
        options = {"name": "dashboard-card", "target_path": "src/app/features"}

        (invocation,) = build_ng_complex_component_invocations(
            config, settings, document="src/app/app.openui.json", **options
        )
        with self.assertRaisesRegex(AngularCommandError, "features are required"):
            build_ng_complex_component_invocations(config, settings, **options)

        self.assertFalse(
            [arg for arg in invocation.argv if arg.startswith("--features")]
        )

    def test_management_commands_forward_the_openui_document(self) -> None:
        from django.core.management import call_command

        cases = {
            "ng_gen_app": {"app_name": "portal"},
            "ng_complex_component": {
                "name": "dashboard-card",
                "target_path": "src/app/features/dashboard",
                "features": "nested",
            },
            "ng_page": {"name": "orders", "target_path": "src/app/features/orders"},
            "ng_component": {"name": "order-card"},
            "ng_reactive_form": {"name": "contact"},
        }
        for command, options in cases.items():
            with self.subTest(command=command):
                stdout = io.StringIO()
                call_command(
                    command,
                    dry_run=True,
                    stdout=stdout,
                    document="src/app/app.openui.json",
                    node_id="root",
                    **options,
                )

                (invocation,) = json.loads(stdout.getvalue())["invocations"]
                self.assertIn("--document=src/app/app.openui.json", invocation["argv"])
                self.assertIn("--node-id=root", invocation["argv"])

        stdout = io.StringIO()
        call_command(
            "ng_workspace",
            dry_run=True,
            stdout=stdout,
            document="src/app/app.openui.json",
        )
        last = json.loads(stdout.getvalue())["invocations"][-1]
        self.assertIn("--document=src/app/app.openui.json", last["argv"])

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
                str(ROOT / "scratch" / "angular" / "ng-openapi-gen.json"),
            ],
        )
        generated_config = ROOT / "scratch" / "angular" / "ng-openapi-gen.json"
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
            str(ROOT / "scratch" / "angular" / "generated" / "ng-openapi-gen"),
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
                f"--openapi-spec-file={schema_path}",
                "--output-path=src/app/api",
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
        self.assertIn("--helpers-path=src/app/api-integration", argv)
        self.assertIn("--skip-helpers=true", argv)
        self.assertIn("--skip-tests=true", argv)

    def test_ng_openapi_setup_dry_run_forwards_auth_scheme(self) -> None:
        exit_code, stdout, stderr = self.run_cli(
            "ng_openapi_setup", "--auth-scheme", "basic", "--dry-run"
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        argv = json.loads(stdout)["invocations"][0]["argv"]
        self.assertIn("--auth-scheme=basic", argv)

    def test_ng_openapi_setup_management_command_forwards_auth_scheme(self) -> None:
        from django.core.management import call_command

        for options, expected in (({"auth_scheme": "basic"}, True), ({}, False)):
            with self.subTest(options=options):
                stdout = io.StringIO()
                call_command("ng_openapi_setup", dry_run=True, stdout=stdout, **options)

                (invocation,) = json.loads(stdout.getvalue())["invocations"]
                self.assertEqual("--auth-scheme=basic" in invocation["argv"], expected)
                self.assertFalse(
                    any(
                        arg.startswith("--auth-scheme=bearer")
                        for arg in invocation["argv"]
                    )
                )

    def test_angular_invocation_normalizes_long_flags(self) -> None:
        invocation = AngularInvocation(
            command_name="ng_test",
            argv=(
                "ng",
                "generate",
                "angular-django2:reactive-form",
                "--authGuard=portalGuard",
                "--openapi_spec_file=openapi.json",
                "--skipTests",
            ),
            cwd=ROOT,
        )

        self.assertEqual(
            invocation.argv,
            (
                "ng",
                "generate",
                "angular-django2:reactive-form",
                "--auth-guard=portalGuard",
                "--openapi-spec-file=openapi.json",
                "--skip-tests",
            ),
        )

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
            [ng, "add", DEFAULT_NG_ADD_PACKAGE, "--skip-confirmation"],
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


class NgdjSchematicInvocationTests(unittest.TestCase):
    """``build_ngdj_schematic_invocations`` runs a schematic with no wrapper."""

    def build(self, **options):
        config = load_project_config(PROJECT_CONFIG_PATH)
        settings = load_angular_settings({"ng_executable": "ng"})
        return build_ngdj_schematic_invocations(config, settings, **options)

    def test_the_schematic_runs_from_the_workspace_with_the_document_element(
        self,
    ) -> None:
        (invocation,) = self.build(
            schematic="tabs", project="shop", document="a.openui.json", node_id="views"
        )

        self.assertEqual(invocation.command_name, "angular-django2:tabs")
        self.assertEqual(
            invocation.argv,
            (
                "ng",
                "generate",
                "angular-django2:tabs",
                "--project=shop",
                "--document=a.openui.json",
                "--node-id=views",
            ),
        )

    def test_name_and_path_are_forwarded_when_given(self) -> None:
        (invocation,) = self.build(
            schematic="table",
            name="orders-grid",
            path="src/app/shared",
            document="a.openui.json",
        )

        self.assertEqual(
            invocation.argv[3:],
            ("orders-grid", "--path=src/app/shared", "--document=a.openui.json"),
        )

    def test_invalid_input_is_refused(self) -> None:
        for options, message in (
            ({"schematic": "tabs"}, "needs an OpenUI document"),
            ({"schematic": "../tabs", "document": "a.json"}, "kebab-case"),
            ({"schematic": "tabs", "document": "/abs.json"}, "relative path"),
            ({"schematic": "tabs", "document": "a.json", "path": "../x"}, "relative"),
            ({"schematic": "tabs", "document": "a.json", "name": "Bad"}, "kebab-case"),
        ):
            with self.subTest(options=options):
                with self.assertRaisesRegex(AngularCommandError, message):
                    self.build(**options)
