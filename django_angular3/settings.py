from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


class AngularCommandError(RuntimeError):
    """Raised when an Angular command cannot be planned or executed."""


@dataclass(frozen=True)
class AngularSettings:
    """Configuration values used to plan and run Angular-related commands."""

    config_path: str = "django-angular3.json"
    node_executable: str = "node"
    npm_executable: str = "npm"
    npx_executable: str = "npx"
    ng_executable: str = "ng"
    package_manager: str = "npm"
    build_configuration: str = "production"
    style: str = "scss"
    routing: bool = True


def load_angular_settings(overrides: Mapping[str, Any] | None = None) -> AngularSettings:
    data = dict(_load_django_settings())
    if overrides:
        data.update(overrides)
    return AngularSettings(**data)


def _load_django_settings() -> Mapping[str, Any]:
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
    return value
