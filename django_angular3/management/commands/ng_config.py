from ._base import AngularBaseCommand


class Command(AngularBaseCommand):
    angular_command_name = "ng_config"
    help = "Apply django-angular3 Angular workspace defaults."
