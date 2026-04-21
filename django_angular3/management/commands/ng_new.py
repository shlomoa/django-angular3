from ._base import AngularBaseCommand


class Command(AngularBaseCommand):
    angular_command_name = "ng_new"
    help = "Create an empty Angular workspace for django-angular3."
