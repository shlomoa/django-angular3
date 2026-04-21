from ._base import AngularBaseCommand


class Command(AngularBaseCommand):
    angular_command_name = "ng_build"
    help = "Build the configured Angular application."
