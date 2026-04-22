import argparse

from django.core.management.base import BaseCommand, CommandError

from ...angular import AngularCommandError, execute_invocations, format_invocations, plan_angular_init


class Command(BaseCommand):
    help = "Initialize an Angular workspace using pnpm by default."

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("project_name", help="Angular workspace project name.")
        parser.add_argument(
            "--folder",
            default=None,
            help="Workspace directory. Defaults to the project name.",
        )
        parser.add_argument(
            "--package",
            default="pnpm",
            help="Angular workspace package manager. Defaults to pnpm.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print the command plan instead of invoking Angular tooling.",
        )

    def handle(self, *args, **options) -> None:
        try:
            invocations = plan_angular_init(
                options["project_name"],
                folder=options.get("folder"),
                package_manager=options.get("package"),
            )
        except (AngularCommandError, TypeError, ValueError) as exc:
            raise CommandError(str(exc)) from exc

        if options["dry_run"]:
            self.stdout.write(format_invocations(invocations))
            return

        try:
            execute_invocations(invocations)
        except AngularCommandError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS(f"Executed {len(invocations)} command(s)."))
