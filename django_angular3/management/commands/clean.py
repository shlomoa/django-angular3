from __future__ import annotations

import argparse

from django.core.management.base import BaseCommand

from ...cleanup import clean_artifact_paths, project_root, remove_artifacts


class Command(BaseCommand):
    help = "Remove temporary build and package artifacts from the current project."

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="List artifacts that would be removed without removing them.",
        )

    def handle(self, *args: object, **options: object) -> None:
        paths = list(clean_artifact_paths(project_root()))
        if options["dry_run"]:
            for path in paths:
                self.stdout.write(str(path))
            return

        for path in remove_artifacts(paths):
            self.stdout.write(f"Removed {path}")
