import argparse

from ._base import (
    AngularBaseCommand,
    add_openui_document_arguments,
    openui_document_options,
)


class Command(AngularBaseCommand):
    angular_command_name = "ng_component"
    help = "Generate a standalone OnPush Angular component."

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        super().add_arguments(parser)
        parser.add_argument("--name", required=True, help="Component name.")
        parser.add_argument("--target-path", default=None)
        parser.add_argument("--project", default=None)
        add_openui_document_arguments(parser)

    def get_invocation_options(self, options: dict[str, object]) -> dict[str, object]:
        return {
            "name": options["name"],
            "target_path": options["target_path"],
            "project": options["project"],
            **openui_document_options(options),
        }
