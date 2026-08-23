import argparse

from ._base import AngularBaseCommand


class Command(AngularBaseCommand):
    angular_command_name = "ng_material_setup"
    help = (
        "Configure Angular Material in an existing project via the "
        "angular-django2:material-setup schematic."
    )

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        super().add_arguments(parser)
        parser.add_argument(
            "--project",
            default=None,
            help="Angular project (defaults to project.name from config).",
        )
        parser.add_argument(
            "--theme",
            default=None,
            help="Angular Material prebuilt theme name.",
        )
        parser.add_argument(
            "--typography",
            action=argparse.BooleanOptionalAction,
            default=None,
            help="Include Material typography styles.",
        )
        parser.add_argument(
            "--animations",
            action=argparse.BooleanOptionalAction,
            default=None,
            help="Enable Angular animations.",
        )

    def get_invocation_options(self, options: dict[str, object]) -> dict[str, object]:
        return {
            "project": options.get("project"),
            "theme": options.get("theme"),
            "typography": options.get("typography"),
            "animations": options.get("animations"),
        }
