from ._base import AngularBaseCommand

class Command(AngularBaseCommand):
    angular_command_name = "ng_workspace_delete"
    help = "Delete the generated Angular workspace entirely."
