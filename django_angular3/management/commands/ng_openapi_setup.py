import argparse

from ._base import AngularBaseCommand


class Command(AngularBaseCommand):
    angular_command_name = "ng_openapi_setup"
    help = (
        "Bootstrap ng-openapi-gen and Django integration helpers via the "
        "angular-django2:openapi-setup schematic."
    )

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        super().add_arguments(parser)
        parser.add_argument(
            "--output-path",
            default="src/app/api",
            help="Output path for generated API clients (default: src/app/api).",
        )
        parser.add_argument(
            "--helpers-path",
            default=None,
            help="Output path for generated Django integration helpers.",
        )
        parser.add_argument(
            "--skip-helpers",
            action="store_true",
            help=(
                "Skip generating Django auth/CSRF/transport and resource-adapter "
                "helpers."
            ),
        )
        parser.add_argument(
            "--skip-tests",
            action="store_true",
            help="Skip generating tests for the integration helpers.",
        )

    def get_invocation_options(self, options: dict[str, object]) -> dict[str, object]:
        return {
            "output_path": options.get("output_path"),
            "helpers_path": options.get("helpers_path"),
            "skip_helpers": options.get("skip_helpers"),
            "skip_tests": options.get("skip_tests"),
        }
