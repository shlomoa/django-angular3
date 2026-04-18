from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from ...angular import AngularCommandError, execute_invocations, format_invocations, plan_angular_command
from ...config import ConfigError


class AngularBaseCommand(BaseCommand):
    angular_command_name = ""

    def add_arguments(self, parser) -> None:
        parser.add_argument("path", nargs="?", default=None, help="Path to the project config.")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print the command plan instead of invoking Angular tooling.",
        )

    def get_plan_options(self, options: dict[str, object]) -> dict[str, object]:
        return {}

    def handle(self, *args, **options) -> None:
        try:
            invocations = plan_angular_command(
                self.angular_command_name,
                options.get("path"),
                **self.get_plan_options(options),
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

        self.stdout.write(self.style.SUCCESS(f"Executed {len(invocations)} command(s)."))
