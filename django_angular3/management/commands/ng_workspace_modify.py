from ._base import AngularBaseCommand


class Command(AngularBaseCommand):
    angular_command_name = "ng_workspace_modify"
    help = "Reapply angular-django2 workspace bootstrap and django-angular3 defaults."
