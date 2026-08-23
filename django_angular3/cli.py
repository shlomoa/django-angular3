from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from .angular import (
    AngularCommandError,
    execute_invocations,
    format_invocations,
    resolve_angular_command_context,
)
from .config import ConfigError, load_project_config
from .validation import (
    validate_openapi_file,
    validate_openui_file,
    validate_project_config,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="django-angular3")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_openapi = subparsers.add_parser(
        "validate-openapi", help="Validate an OpenAPI source document."
    )
    validate_openapi.add_argument("path", help="Path to the OpenAPI document.")

    validate_openui = subparsers.add_parser(
        "validate-openui", help="Validate a UI definition document."
    )
    validate_openui.add_argument("path", help="Path to the UI definition document.")

    subparsers.add_parser(
        "validate-project", help="Validate a django-angular3 project configuration."
    )

    ng_new = subparsers.add_parser("ng_new", help="Create an empty Angular workspace.")
    ng_new.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Print discovered configuration, derived paths, and resolved "
            "Angular subprocess calls instead of invoking Angular tooling."
        ),
    )

    ng_workspace = subparsers.add_parser(
        "ng_workspace",
        help="Bootstrap the configured Angular workspace with angular-django2.",
    )
    ng_workspace.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Print discovered configuration, derived paths, and resolved "
            "Angular subprocess calls instead of invoking Angular tooling."
        ),
    )

    ng_config = subparsers.add_parser(
        "ng_config", help="Configure Angular workspace defaults."
    )
    ng_config.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Print discovered configuration, derived paths, and resolved "
            "Angular subprocess calls instead of invoking Angular tooling."
        ),
    )

    ng_build = subparsers.add_parser(
        "ng_build", help="Build the configured Angular application."
    )
    ng_build.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Print discovered configuration, derived paths, and resolved "
            "Angular subprocess calls instead of invoking Angular tooling."
        ),
    )

    ng_gen_app = subparsers.add_parser(
        "ng_gen_app",
        help="Generate an Angular application in the configured workspace.",
    )
    ng_gen_app.add_argument(
        "--app-name", default=None, help="Optional Angular application name."
    )
    ng_gen_app.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Print discovered configuration, derived paths, and resolved "
            "Angular subprocess calls instead of invoking Angular tooling."
        ),
    )

    ng_complex_component = subparsers.add_parser(
        "ng_complex_component",
        help="Generate, update, or delete an advanced Angular Material component.",
    )
    ng_complex_component.add_argument("--name", required=True, help="Kebab-case name.")
    ng_complex_component.add_argument(
        "--target-path",
        required=True,
        help="Path within the Angular application source tree.",
    )
    ng_complex_component.add_argument(
        "--features",
        required=True,
        help="Comma-separated features: mixins, nested, projection, cdk-overlay.",
    )
    ng_complex_component.add_argument(
        "--project", default=None, help="Angular project."
    )
    ng_complex_component.add_argument(
        "--mode", choices=["create", "modify", "delete"], default="create"
    )
    ng_complex_component.add_argument(
        "--confirm", action="store_true", help="Required when --mode=delete."
    )
    ng_complex_component.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Print discovered configuration, derived paths, and resolved "
            "Angular subprocess calls instead of invoking Angular tooling."
        ),
    )

    ng_openapi_gen = subparsers.add_parser(
        "ng_openapi_gen", help="Run ng-openapi-gen for the configured OpenAPI source."
    )
    ng_openapi_gen.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Print discovered configuration, derived paths, and resolved "
            "Angular subprocess calls instead of invoking Angular tooling."
        ),
    )

    ng_openapi_setup = subparsers.add_parser(
        "ng_openapi_setup",
        help=(
            "Bootstrap ng-openapi-gen and Django integration helpers via the "
            "angular-django2:openapi-setup schematic."
        ),
    )
    ng_openapi_setup.add_argument(
        "--output-path",
        default="src/app/api",
        help="Output path for generated API clients (default: src/app/api).",
    )
    ng_openapi_setup.add_argument(
        "--helpers-path",
        default=None,
        help="Output path for generated Django integration helpers.",
    )
    ng_openapi_setup.add_argument(
        "--skip-helpers",
        action="store_true",
        help="Skip generating Django auth/CSRF/transport and resource-adapter helpers.",
    )
    ng_openapi_setup.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip generating tests for the integration helpers.",
    )
    ng_openapi_setup.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Print discovered configuration, derived paths, and resolved "
            "Angular subprocess calls instead of invoking Angular tooling."
        ),
    )

    ng_data_service = subparsers.add_parser(
        "ng_data_service",
        help=(
            "Generate a typed data-service wrapper for a resource via the "
            "angular-django2:data-service schematic."
        ),
    )
    ng_data_service.add_argument(
        "--resource", required=True, help="Resource name for the generated service."
    )
    ng_data_service.add_argument(
        "--project",
        default=None,
        help="Angular project (defaults to project.name from config).",
    )
    ng_data_service.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Print discovered configuration, derived paths, and resolved "
            "Angular subprocess calls instead of invoking Angular tooling."
        ),
    )

    ng_material_setup = subparsers.add_parser(
        "ng_material_setup",
        help=(
            "Configure Angular Material in an existing project via the "
            "angular-django2:material-setup schematic."
        ),
    )
    ng_material_setup.add_argument(
        "--project",
        default=None,
        help="Angular project (defaults to project.name from config).",
    )
    ng_material_setup.add_argument(
        "--theme",
        default=None,
        help="Angular Material prebuilt theme name.",
    )
    ng_material_setup.add_argument(
        "--typography",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Include Material typography styles.",
    )
    ng_material_setup.add_argument(
        "--animations",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable Angular animations.",
    )
    ng_material_setup.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Print discovered configuration, derived paths, and resolved "
            "Angular subprocess calls instead of invoking Angular tooling."
        ),
    )

    ng_add = subparsers.add_parser("ng_add", help="Run ng add for an Angular package.")
    ng_add.add_argument(
        "--package",
        default=None,
        help="Package to add (defaults to setting: ng_add_package).",
    )
    ng_add.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Print discovered configuration, derived paths, and resolved "
            "Angular subprocess calls instead of invoking Angular tooling."
        ),
    )

    install_tutorial = subparsers.add_parser(
        "install-tutorial",
        help="Install the simple_crm tutorial project to a local directory.",
    )
    install_tutorial.add_argument(
        "dest",
        nargs="?",
        default="simple_crm",
        help="Destination directory (default: simple_crm).",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "validate-openapi":
        return _run_validation(
            validate_openapi_file(args.path), f"OpenAPI document {args.path}"
        )

    if args.command == "validate-openui":
        return _run_validation(
            validate_openui_file(args.path), f"UI document {args.path}"
        )

    if args.command == "validate-project":
        try:
            config = load_project_config()
        except ConfigError as exc:
            print(f"Configuration error: {exc}", file=sys.stderr)
            return 1
        return _run_validation(
            validate_project_config(config),
            f"Project configuration {config.config_path}",
        )

    if args.command == "install-tutorial":
        return _run_install_tutorial(args.dest)

    if args.command in {
        "ng_new",
        "ng_workspace",
        "ng_config",
        "ng_build",
        "ng_gen_app",
        "ng_complex_component",
        "ng_openapi_gen",
        "ng_openapi_setup",
        "ng_data_service",
        "ng_material_setup",
        "ng_add",
    }:
        plan_options: dict[str, str | bool | None] = {}
        if args.command == "ng_gen_app":
            plan_options["app_name"] = args.app_name
        if args.command == "ng_add":
            plan_options["package"] = args.package
        if args.command == "ng_openapi_setup":
            plan_options = {
                "output_path": args.output_path,
                "helpers_path": args.helpers_path,
                "skip_helpers": args.skip_helpers,
                "skip_tests": args.skip_tests,
            }
        if args.command == "ng_data_service":
            plan_options = {
                "resource": args.resource,
                "project": args.project,
            }
        if args.command == "ng_material_setup":
            plan_options = {
                "project": args.project,
                "theme": args.theme,
                "typography": args.typography,
                "animations": args.animations,
            }
        if args.command == "ng_complex_component":
            plan_options = {
                "name": args.name,
                "target_path": args.target_path,
                "features": args.features,
                "project": args.project,
                "mode": args.mode,
                "confirm": args.confirm,
            }
        return _run_angular_command(args.command, dry_run=args.dry_run, **plan_options)

    parser.error("Unknown command")
    return 2


def _run_validation(errors: list[str], label: str) -> int:
    if errors:
        print(f"{label} is invalid.", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(f"{label} is valid.")
    return 0


def _run_angular_command(
    command_name: str, *, dry_run: bool, **options: str | bool | None
) -> int:
    try:
        config, settings, invocations = resolve_angular_command_context(
            command_name, **options
        )
    except (AngularCommandError, ConfigError, TypeError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1

    if dry_run:
        print(format_invocations(invocations, config, settings))
        return 0

    try:
        execute_invocations(invocations, settings)
    except AngularCommandError as exc:
        print(exc, file=sys.stderr)
        return 1

    print(f"Executed {len(invocations)} command(s).")
    return 0


def _run_install_tutorial(dest: str) -> int:
    import shutil

    src = Path(__file__).parent / "examples" / "01_simple_crm"
    dest_path = Path(dest)

    if dest_path.exists():
        print(f"Error: destination '{dest_path}' already exists.", file=sys.stderr)
        return 1

    shutil.copytree(
        src,
        dest_path,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )
    print(f"Tutorial project installed to '{dest_path}'.")
    print()
    print("Next steps:")
    print(f"  cd {dest_path}")
    print("  python manage.py migrate")
    print("  python manage.py createsuperuser")
    print("  python manage.py runserver")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
