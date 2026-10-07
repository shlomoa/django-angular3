import argparse

from ._base import (
    AngularBaseCommand,
    add_openui_document_arguments,
    openui_document_options,
)


class Command(AngularBaseCommand):
    angular_command_name = "ng_workspace"
    help = "Create and bootstrap an Angular workspace with angular-django2."

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        super().add_arguments(parser)
        add_openui_document_arguments(parser, node_id=False)

    def get_invocation_options(self, options: dict[str, object]) -> dict[str, object]:
        return openui_document_options(options, node_id=False)
