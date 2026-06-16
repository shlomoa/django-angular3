from __future__ import annotations

import argparse

from django.core.management.base import BaseCommand, CommandError

from ...angular import (
    AngularCommandError,
    execute_invocations,
    format_invocations,
    resolve_angular_command,
)
from ...config import ConfigError


class AngularBaseCommand(BaseCommand):
    """Base class for django-angular3 management commands that wrap
    Angular tooling."""

    angular_command_name = ""

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "path", nargs="?", default=None, help="Path to the project config."
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help=(
                "Print the resolved subprocess call list instead of invoking "
                "Angular tooling."
            ),
        )

    def get_invocation_options(self, _options: dict[str, object]) -> dict[str, object]:
        return {}

    def handle(self, *args, **options) -> None:
        try:
            invocations = resolve_angular_command(
                self.angular_command_name,
                options.get("path"),
                **self.get_invocation_options(options),
            )
        except (AngularCommandError, ConfigError, TypeError, ValueError) as exc:
            raise CommandError(str(exc)) from exc

        if options["dry_run"]:
            self.stdout.write(format_invocations(invocations))
            return

        try:
            execute_invocations(invocations)
        except AngularCommandError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(f"Executed {len(invocations)} command(s).")
