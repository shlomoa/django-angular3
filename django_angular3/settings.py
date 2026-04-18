from types import SimpleNamespace


class AngularCommandError(RuntimeError):
    """Raised when an Angular command cannot be planned or executed."""


DEFAULT_ANGULAR_SETTINGS = {
    "config_path": "django-angular3.json",
    "node_executable": "node",
    "npm_executable": "npm",
    "npx_executable": "npx",
    "ng_executable": "ng",
    "package_manager": "npm",
    "build_configuration": "production",
    "style": "scss",
    "routing": True,
}


class AngularSettings(SimpleNamespace):
    """Configuration values used to plan and run Angular-related commands."""


def load_angular_settings(overrides=None):
    data = DEFAULT_ANGULAR_SETTINGS.copy()
    data.update(_load_django_settings())
    if overrides:
        data.update(overrides)
    return AngularSettings(**data)


def _load_django_settings():
    try:
        from django.conf import settings as django_settings
        from django.core.exceptions import ImproperlyConfigured
    except ImportError:
        return {}

    try:
        if not getattr(django_settings, "configured", False):
            return {}

        value = getattr(django_settings, "DJANGO_ANGULAR3", {})
    except ImproperlyConfigured:
        return {}

    if not hasattr(value, "items"):
        raise AngularCommandError(
            f"DJANGO_ANGULAR3 must be a dictionary-like mapping, got {type(value).__name__}."
        )

    return dict(value)
