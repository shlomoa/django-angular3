from collections.abc import Mapping
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
    """Configuration values used to plan and run Angular-related commands.

    Attributes:
        config_path (str): Default project config path.
        node_executable (str): Node executable name or path.
        npm_executable (str): npm executable name or path.
        npx_executable (str): npx executable name or path.
        ng_executable (str): Angular CLI executable name or path.
        package_manager (str): Angular package manager setting.
        build_configuration (str): Angular build configuration name.
        style (str): Default Angular stylesheet format.
        routing (bool): Whether generated applications enable routing.
    """


def load_angular_settings(overrides: Mapping[str, object] | None = None) -> AngularSettings:
    data = DEFAULT_ANGULAR_SETTINGS.copy()
    data.update(_load_django_settings())
    if overrides:
        data.update(overrides)
    return AngularSettings(**data)


def _load_django_settings() -> dict[str, object]:
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

    if not isinstance(value, Mapping):
        raise AngularCommandError(
            f"DJANGO_ANGULAR3 must be a dictionary-like mapping, got {type(value).__name__}."
        )

    return dict(value)
