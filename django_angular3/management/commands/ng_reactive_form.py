import argparse

from ._base import (
    AngularBaseCommand,
    add_openui_document_arguments,
    openui_document_options,
)


class Command(AngularBaseCommand):
    angular_command_name = "ng_reactive_form"
    help = "Generate a typed Angular Material reactive form."

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        super().add_arguments(parser)
        parser.add_argument("--name", required=True, help="Kebab-case form name.")
        parser.add_argument(
            "--definition",
            default=None,
            help="Deprecated form definition file; use --document instead.",
        )
        parser.add_argument("--target-path", default=None)
        parser.add_argument("--project", default=None)
        parser.add_argument("--primitives-path", default=None)
        add_openui_document_arguments(parser)

    def get_invocation_options(self, options: dict[str, object]) -> dict[str, object]:
        return {
            "name": options["name"],
            "definition": options["definition"],
            "target_path": options["target_path"],
            "project": options["project"],
            "primitives_path": options["primitives_path"],
            **openui_document_options(options),
        }
