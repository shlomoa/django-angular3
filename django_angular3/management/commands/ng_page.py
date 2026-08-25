import argparse

from ._base import AngularBaseCommand


class Command(AngularBaseCommand):
    angular_command_name = "ng_page"
    help = "Generate a routed Angular Material page."

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        super().add_arguments(parser)
        parser.add_argument("--name", required=True, help="Kebab-case page name.")
        parser.add_argument("--target-path", required=True)
        parser.add_argument("--project", default=None)
        parser.add_argument("--route-path", default=None)
        parser.add_argument(
            "--access", choices=["public", "protected"], default="public"
        )
        parser.add_argument("--auth-guard", default="authGuard")
        parser.add_argument("--navigation-label", default=None)
        parser.add_argument("--navigation-icon", default=None)

    def get_invocation_options(self, options: dict[str, object]) -> dict[str, object]:
        return {
            "name": options["name"],
            "target_path": options["target_path"],
            "project": options["project"],
            "route_path": options["route_path"],
            "access": options["access"],
            "auth_guard": options["auth_guard"],
            "navigation_label": options["navigation_label"],
            "navigation_icon": options["navigation_icon"],
        }
