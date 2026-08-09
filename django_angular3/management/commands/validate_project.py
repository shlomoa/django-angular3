"""Management command: validate_project.

Validate the discovered django-angular3-project.json and its referenced OAS
and OpenUI sources.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from ...config import ConfigError, load_project_config
from ...validation import validate_project_config


class Command(BaseCommand):
    help = "Validate the project config and its referenced OpenAPI and OpenUI sources."

    def handle(self, *args, **options) -> None:
        try:
            config = load_project_config()
        except ConfigError as exc:
            raise CommandError(str(exc)) from exc

        errors = validate_project_config(config)
        if errors:
            for error in errors:
                self.stderr.write(self.style.ERROR(error))
            raise CommandError("Validation failed.")

        self.stdout.write(self.style.SUCCESS("Project configuration is valid."))
