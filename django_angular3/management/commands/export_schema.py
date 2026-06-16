"""Management command: export_schema

Export the OpenAPI schema from DRF using drf-spectacular and persist it as a
durable, versioned artifact at the path configured in ``openapi.source``.

Before writing, the command rotates the existing schema to its ``.previous``
counterpart (e.g. ``api.json`` → ``api.previous.json``) so that ``build_app``
can compare the two versions for change detection without requiring the caller
to manage file paths explicitly.

Usage::

    django-admin export_schema django-angular3.json
    django-admin export_schema django-angular3.json --format yaml
    django-admin export_schema django-angular3.json --dry-run
"""

from __future__ import annotations

import argparse

from django.core.management.base import BaseCommand, CommandError

from ...config import ConfigError, get_previous_schema_path, load_project_config


class Command(BaseCommand):
    help = (
        "Export the OpenAPI schema from DRF (via drf-spectacular) and persist "
        "it as a versioned artifact. The previous schema is archived alongside "
        "the current one for use by build_app change detection."
    )

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "config",
            help="Path to the django-angular3.json project config file.",
        )
        parser.add_argument(
            "--format",
            dest="format",
            choices=["json", "yaml"],
            default="json",
            help="Serialization format for the exported schema (default: json).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help=(
                "Generate the schema and display the artifact paths that would be "
                "written, but do not modify any files on disk."
            ),
        )

    def handle(self, *args, **options) -> None:
        try:
            config = load_project_config(options["config"])
        except ConfigError as exc:
            raise CommandError(str(exc)) from exc

        destination = config.openapi_source
        previous_path = get_previous_schema_path(destination)

        if options["dry_run"]:
            self.stdout.write("--- DRY RUN: export_schema ---")
            self.stdout.write(f"  destination : {destination}")
            if destination.exists():
                self.stdout.write(
                    f"  previous    : {previous_path}  (would archive current)"
                )
            self.stdout.write("  (no files written)")
            return

        # Generate the schema via drf-spectacular.
        try:
            from drf_spectacular.generators import (
                SchemaGenerator,  # type: ignore[import-untyped]
            )
            from drf_spectacular.renderers import (  # type: ignore[import-untyped]
                OpenApiJsonRenderer,
                OpenApiYamlRenderer,
            )
        except ImportError as exc:  # pragma: no cover
            raise CommandError(
                "drf-spectacular is required for schema export. "
                "Install it with: pip install drf-spectacular"
            ) from exc

        generator = SchemaGenerator()
        schema = generator.get_schema(request=None, public=True)

        renderer = (
            OpenApiYamlRenderer()
            if options["format"] == "yaml"
            else OpenApiJsonRenderer()
        )
        schema_bytes: bytes = renderer.render(schema, renderer_context={})

        # Rotate current → previous before writing the new schema.
        if destination.exists():
            destination.replace(previous_path)
            self.stdout.write(f"Previous schema archived to: {previous_path}")

        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(schema_bytes)
        self.stdout.write(self.style.SUCCESS(f"Schema exported to: {destination}"))
