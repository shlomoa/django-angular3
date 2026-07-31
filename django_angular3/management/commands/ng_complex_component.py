import argparse

from ._base import AngularBaseCommand


class Command(AngularBaseCommand):
    angular_command_name = "ng_complex_component"
    help = "Generate, update, or delete an advanced Angular Material component."

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        super().add_arguments(parser)
        parser.add_argument("--name", required=True, help="Kebab-case component name.")
        parser.add_argument(
            "--target-path",
            required=True,
            help="Path within the Angular application source tree.",
        )
        parser.add_argument(
            "--features",
            required=True,
            help="Comma-separated features: mixins, nested, projection, cdk-overlay.",
        )
        parser.add_argument("--project", default=None, help="Angular project name.")
        parser.add_argument(
            "--mode", choices=["create", "modify", "delete"], default="create"
        )
        parser.add_argument(
            "--confirm", action="store_true", help="Required when --mode=delete."
        )

    def get_invocation_options(self, options: dict[str, object]) -> dict[str, object]:
        return {
            "name": options["name"],
            "target_path": options["target_path"],
            "features": options["features"],
            "project": options["project"],
            "mode": options["mode"],
            "confirm": options["confirm"],
        }
