from __future__ import annotations

import argparse

from django.core.management.base import BaseCommand, CommandError

from ...cleanup import project_root
from ...command_execution import run_command


class Command(BaseCommand):
    help = "Remove all untracked files and directories from the current Git worktree."

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="List untracked files that would be removed without removing them.",
        )

    def handle(self, *args: object, **options: object) -> None:
        argv = ["git", "clean", "-f", "-d"]
        if options["dry_run"]:
            argv.append("-n")

        result = run_command(argv, cwd=project_root(), check=False)
        if result.returncode:
            raise CommandError(result.stderr.strip() or "git clean failed.")

        if result.stdout:
            self.stdout.write(result.stdout, ending="")
