from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from .angular import (
    AngularCommandError,
    execute_invocations,
    format_invocations,
    resolve_angular_command,
)
from .build import create_build_plan, write_build_plan
from .config import ConfigError, load_project_config
from .validation import validate_openapi_file, validate_project_config, validate_ui_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="django-angular3")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_openapi = subparsers.add_parser(
        "validate-openapi", help="Validate an OpenAPI source document."
    )
    validate_openapi.add_argument("path", help="Path to the OpenAPI document.")

    validate_ui = subparsers.add_parser(
        "validate-ui", help="Validate a UI definition document."
    )
    validate_ui.add_argument("path", help="Path to the UI definition document.")

    validate_project = subparsers.add_parser(
        "validate-project", help="Validate a django-angular3 project configuration."
    )
    validate_project.add_argument(
        "path",
        nargs="?",
        default="django-angular3.json",
        help="Path to the project config.",
    )

    build = subparsers.add_parser(
        "build", help="Validate a project and emit a deterministic build plan."
    )
    build.add_argument(
        "path", nargs="?", default="django-angular3.json", help="Path to the config."
    )
    build.add_argument(
        "--output",
        default="build",
        help="Directory where the build plan should be written.",
    )
    build.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the build plan instead of writing it to disk.",
    )

    ng_new = subparsers.add_parser("ng_new", help="Create an empty Angular workspace.")
    ng_new.add_argument(
        "path", nargs="?", default=None, help="Path to the project config."
    )
    ng_new.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Print the resolved Angular subprocess call list instead of "
            "invoking Angular tooling."
        ),
    )

    ng_workspace = subparsers.add_parser(
        "ng_workspace",
        help="Bootstrap the configured Angular workspace with angular-django2.",
    )
    ng_workspace.add_argument(
        "path", nargs="?", default=None, help="Path to the project config."
    )
    ng_workspace.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Print the resolved Angular subprocess call list instead of "
            "invoking Angular tooling."
        ),
    )

    ng_config = subparsers.add_parser(
        "ng_config", help="Configure Angular workspace defaults."
    )
    ng_config.add_argument(
        "path", nargs="?", default=None, help="Path to the project config."
    )
    ng_config.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Print the resolved Angular subprocess call list instead of "
            "invoking Angular tooling."
        ),
    )

    ng_build = subparsers.add_parser(
        "ng_build", help="Build the configured Angular application."
    )
    ng_build.add_argument(
        "path", nargs="?", default=None, help="Path to the project config."
    )
    ng_build.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Print the resolved Angular subprocess call list instead of "
            "invoking Angular tooling."
        ),
    )

    ng_gen_app = subparsers.add_parser(
        "ng_gen_app",
        help="Generate an Angular application in the configured workspace.",
    )
    ng_gen_app.add_argument(
        "path", nargs="?", default=None, help="Path to the project config."
    )
    ng_gen_app.add_argument(
        "--app-name", default=None, help="Optional Angular application name."
    )
    ng_gen_app.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Print the resolved Angular subprocess call list instead of "
            "invoking Angular tooling."
        ),
    )

    ng_openapi_gen = subparsers.add_parser(
        "ng_openapi_gen", help="Run ng-openapi-gen for the configured OpenAPI source."
    )
    ng_openapi_gen.add_argument(
        "path", nargs="?", default=None, help="Path to the project config."
    )
    ng_openapi_gen.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Print the resolved Angular subprocess call list instead of "
            "invoking Angular tooling."
        ),
    )

    ng_add = subparsers.add_parser("ng_add", help="Run ng add for an Angular package.")
    ng_add.add_argument(
        "path", nargs="?", default=None, help="Path to the project config."
    )
    ng_add.add_argument(
        "--package",
        default=None,
        help="Package to add (defaults to setting: ng_add_package).",
    )
    ng_add.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Print the resolved Angular subprocess call list instead of "
            "invoking Angular tooling."
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

    if args.command == "validate-ui":
        return _run_validation(validate_ui_file(args.path), f"UI document {args.path}")

    if args.command == "validate-project":
        try:
            config = load_project_config(args.path)
        except ConfigError as exc:
            print(f"Configuration error: {exc}", file=sys.stderr)
            return 1
        return _run_validation(
            validate_project_config(config), f"Project configuration {Path(args.path)}"
        )

    if args.command == "build":
        try:
            config = load_project_config(args.path)
        except ConfigError as exc:
            print(f"Configuration error: {exc}", file=sys.stderr)
            return 1

        errors = validate_project_config(config)
        if errors:
            return _run_validation(errors, f"Project configuration {Path(args.path)}")

        plan = create_build_plan(config)
        if args.dry_run:
            print(json.dumps(plan.to_dict(), indent=2))
            return 0

        plan_path = write_build_plan(plan, args.output)
        print(f"Wrote build plan to {plan_path}")
        return 0

    if args.command == "install-tutorial":
        return _run_install_tutorial(args.dest)

    if args.command in {
        "ng_new",
        "ng_workspace",
        "ng_config",
        "ng_build",
        "ng_gen_app",
        "ng_openapi_gen",
        "ng_add",
    }:
        plan_options = {}
        if args.command == "ng_gen_app":
            plan_options["app_name"] = args.app_name
        if args.command == "ng_add":
            plan_options["package"] = args.package
        return _run_angular_command(
            args.command, args.path, dry_run=args.dry_run, **plan_options
        )

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
    command_name: str, path: str | Path | None, *, dry_run: bool, **options: str | None
) -> int:
    try:
        invocations = resolve_angular_command(command_name, path, **options)
    except (AngularCommandError, ConfigError, TypeError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1

    if dry_run:
        print(format_invocations(invocations))
        return 0

    try:
        execute_invocations(invocations)
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
