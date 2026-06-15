from ._base import AngularBaseCommand


class Command(AngularBaseCommand):
    angular_command_name = "ng_workspace"
    help = "Create and bootstrap an Angular workspace with angular-django2."
