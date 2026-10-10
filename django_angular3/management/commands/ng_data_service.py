import argparse

from ._base import AngularBaseCommand


class Command(AngularBaseCommand):
    angular_command_name = "ng_data_service"
    help = (
        "Generate a typed data-service wrapper for a resource via the "
        "angular-django2:data-service schematic."
    )

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        super().add_arguments(parser)
        parser.add_argument(
            "--resource",
            required=True,
            help="Resource name for the generated service.",
        )
        parser.add_argument(
            "--project",
            default=None,
            help="Angular project (defaults to project.name from config).",
        )

        parser.add_argument(
            "--path",
            default=None,
            help=(
                "Destination path of the generated service, passed to the "
                "schematic (default: the schematic's own default)."
            ),
        )

    def get_invocation_options(self, options: dict[str, object]) -> dict[str, object]:
        return {
            "resource": options.get("resource"),
            "project": options.get("project"),
            "path": options.get("path"),
        }
