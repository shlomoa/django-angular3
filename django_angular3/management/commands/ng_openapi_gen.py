from ._base import AngularBaseCommand


class Command(AngularBaseCommand):
    angular_command_name = "ng_openapi_gen"
    help = "Run ng-openapi-gen for the configured OpenAPI source."
