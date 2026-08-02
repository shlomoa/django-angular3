"""Management command: validate_project

Validate the django-angular3.json project config and its referenced OpenAPI
and UI sources.

Usage::

    django-admin validate_project django-angular3.json
"""

from __future__ import annotations

import argparse

from django.core.management.base import BaseCommand, CommandError

from ...config import ConfigError, load_project_config
from ...validation import validate_project_config


class Command(BaseCommand):
    help = "Validate the project config and its referenced OpenAPI and UI sources."

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "config",
            nargs="?",
            default="django-angular3.json",
            help="Path to the django-angular3.json config file (default: django-angular3.json).",  # noqa: E501
        )

    def handle(self, *args, **options) -> None:
        try:
            config = load_project_config(options["config"])
        except ConfigError as exc:
            raise CommandError(str(exc)) from exc

        errors = validate_project_config(config)
        if errors:
            for error in errors:
                self.stderr.write(self.style.ERROR(error))
            raise CommandError("Validation failed.")

        self.stdout.write(self.style.SUCCESS("Project configuration is valid."))
