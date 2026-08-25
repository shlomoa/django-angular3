import argparse

from ._base import AngularBaseCommand


class Command(AngularBaseCommand):
    angular_command_name = "ng_site"
    help = "Assemble or maintain an OpenUI-defined Material site."

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        super().add_arguments(parser)
        source = parser.add_mutually_exclusive_group()
        source.add_argument("--source", default=None)
        source.add_argument("--defaults", action="store_true")
        parser.add_argument("--project", default=None)
        parser.add_argument(
            "--operation", choices=["create", "modify", "delete"], default="create"
        )
        parser.add_argument("--confirm-delete", action="store_true")
        parser.add_argument("--auth-guard", default="authGuard")
        parser.add_argument("--csrf-cookie-name", default="csrftoken")
        parser.add_argument("--csrf-header-name", default="X-CSRFToken")

    def get_invocation_options(self, options: dict[str, object]) -> dict[str, object]:
        return {
            "source": options["source"],
            "defaults": options["defaults"],
            "project": options["project"],
            "operation": options["operation"],
            "confirm_delete": options["confirm_delete"],
            "auth_guard": options["auth_guard"],
            "csrf_cookie_name": options["csrf_cookie_name"],
            "csrf_header_name": options["csrf_header_name"],
        }
