import argparse

from ._base import AngularBaseCommand


class Command(AngularBaseCommand):
    angular_command_name = "ng_add"
    help = "Run ng add for an Angular package in the configured workspace."

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        super().add_arguments(parser)
        parser.add_argument(
            "--package",
            default=None,
            help="Package to add (defaults to setting: ng_add_package).",
        )

    def get_plan_options(self, options: dict[str, object]) -> dict[str, object]:
        return {"package": options.get("package")}
