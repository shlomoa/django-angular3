from ._base import AngularBaseCommand


class Command(AngularBaseCommand):
    angular_command_name = "ng_gen_app"
    help = "Generate an Angular application inside the configured workspace."

    def add_arguments(self, parser) -> None:
        super().add_arguments(parser)
        parser.add_argument(
            "--app-name",
            default=None,
            help="Optional Angular application name. Defaults to project.name from config.",
        )

    def get_plan_options(self, options: dict[str, object]) -> dict[str, object]:
        return {"app_name": options.get("app_name")}
