from collections.abc import Mapping, Sequence
from types import SimpleNamespace


class AngularCommandError(RuntimeError):
    """Raised when an Angular command cannot be planned or executed."""


DEFAULT_ANGULAR_SETTINGS = {
    "config_path": "django-angular3.json",
    "node_executable": "node",
    "pnpm_executable": "pnpm",
    "ng_executable": "ng",
    "command_allowlist": ("ng_openapi_gen",),
    "package_manager": "pnpm",
    "build_configuration": "production",
    "style": "scss",
    "routing": True,
}


class AngularSettings(SimpleNamespace):
    """Configuration values used to plan and run Angular-related commands.

    Attributes:
        config_path (str): Default project config path.
        node_executable (str): Node executable name or path.
        pnpm_executable (str): pnpm executable name or path.
        ng_executable (str): Angular CLI executable name or path.
        command_allowlist (tuple[str, ...]): Allowed django-angular3 command names.
        package_manager (str): Angular package manager setting.
        build_configuration (str): Angular build configuration name.
        style (str): Default Angular stylesheet format.
        routing (bool): Whether generated applications enable routing.
    """


def load_angular_settings(overrides: Mapping[str, object] | None = None) -> AngularSettings:
    data = DEFAULT_ANGULAR_SETTINGS.copy()
    data.update(_normalize_legacy_settings(_load_django_settings()))
    if overrides:
        data.update(_normalize_legacy_settings(overrides))
    data["command_allowlist"] = _normalize_command_allowlist(data.get("command_allowlist"))
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


def _normalize_legacy_settings(data: Mapping[str, object]) -> dict[str, object]:
    normalized = dict(data)
    if "pnpm_executable" not in normalized:
        for legacy_key in ("npx_executable", "npm_executable"):
            if legacy_key in normalized:
                normalized["pnpm_executable"] = normalized[legacy_key]
                break

    normalized.pop("npm_executable", None)
    normalized.pop("npx_executable", None)
    return normalized


def _normalize_command_allowlist(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        commands = (value,)
    elif isinstance(value, Sequence):
        commands = tuple(value)
    else:
        raise AngularCommandError(
            "DJANGO_ANGULAR3['command_allowlist'] must be a string or a sequence of strings."
        )

    normalized_commands: list[str] = []
    for command in commands:
        if not isinstance(command, str):
            raise AngularCommandError(
                "DJANGO_ANGULAR3['command_allowlist'] must only contain strings."
            )

        normalized_command = command.strip().lower()
        if not normalized_command:
            raise AngularCommandError(
                "DJANGO_ANGULAR3['command_allowlist'] cannot contain empty command names."
            )

        if normalized_command not in normalized_commands:
            normalized_commands.append(normalized_command)

    return tuple(normalized_commands)
