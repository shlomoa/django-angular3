import os
from collections.abc import Generator, Mapping, Sequence
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from .documents import DocumentError, load_document


class AngularCommandError(RuntimeError):
    """Raised when an Angular command cannot be resolved or executed."""


_is_win = os.name == "nt"

DEFAULT_ANGULAR_SETTINGS: dict[str, Any] = {
    "config_path": "django-angular3.json",
    "node_executable": "node.exe" if _is_win else "node",
    "pnpm_executable": "pnpm.cmd" if _is_win else "pnpm",
    "ng_executable": "ng.cmd" if _is_win else "ng",
    "command_allowlist": ("ng_openapi_gen",),
    "package_manager": "pnpm",
    "build_configuration": "production",
    "style": "scss",
    "routing": True,
    "ssr": False,
    "zoneless": True,
    "ng_add_package": "angular-django2",
}


class AngularSettings(SimpleNamespace):
    """Configuration values used to resolve and run Angular-related commands.

    Attributes:
        config_path (str): Default project config path.
        node_executable (str): Node executable name or path.
        pnpm_executable (str): pnpm executable name or path.
        ng_executable (str): Angular CLI executable name or path.
        command_allowlist (tuple[str, ...]): Allowed resolved
            django-angular3 command names.
        package_manager (str): Angular package manager setting.
        build_configuration (str): Angular build configuration name.
        style (str): Default Angular stylesheet format.
        routing (bool): Whether generated applications enable routing.
        ssr (bool): Whether generated applications enable server-side rendering.
        zoneless (bool): Whether generated applications use zoneless change
            detection.
        ng_add_package (str): The default package name or path to install for ng_add.
    """


def load_angular_settings(
    overrides: Mapping[str, object] | None = None,
    *,
    config_path: str | Path | None = None,
) -> AngularSettings:
    data = DEFAULT_ANGULAR_SETTINGS.copy()
    data.update(_load_tool_configuration(config_path))
    if overrides:
        data.update(overrides)
    data["command_allowlist"] = _normalize_command_allowlist(
        data.get("command_allowlist")
    )
    return AngularSettings(**data)


def _load_tool_configuration(
    config_path: str | Path | None,
) -> dict[str, object]:
    path = Path(config_path or DEFAULT_ANGULAR_SETTINGS["config_path"])
    if not path.is_file():
        return {}

    try:
        document = load_document(path)
    except DocumentError as exc:
        raise AngularCommandError(str(exc)) from exc
    if not isinstance(document, Mapping):
        raise AngularCommandError(
            "django-angular3 tool configuration must be a mapping."
        )

    errors = validate_tool_configuration(document)
    if errors:
        raise AngularCommandError(
            "Invalid django-angular3 tool configuration: " + "; ".join(errors)
        )

    angular = _optional_mapping(document, "angular")
    workspace = _optional_mapping(angular, "workspace")
    application = _optional_mapping(angular, "application")
    build = _optional_mapping(angular, "build")
    tool = _optional_mapping(document, "tool")
    executables = _optional_mapping(tool, "executables")

    values: dict[str, object] = {
        "config_path": str(path),
        "package_manager": workspace.get("packageManager", "pnpm"),
        "style": workspace.get("style", "scss"),
        "routing": workspace.get("routing", True),
        "ssr": application.get("ssr", False),
        "zoneless": application.get("zoneless", True),
        "build_configuration": build.get("configuration", "production"),
        "command_allowlist": tool.get("commandAllowlist", ("ng_openapi_gen",)),
        "ng_add_package": tool.get("ngAddPackage", "angular-django2"),
    }
    for config_key, setting_key in (
        ("node", "node_executable"),
        ("pnpm", "pnpm_executable"),
        ("ng", "ng_executable"),
    ):
        if config_key in executables:
            values[setting_key] = executables[config_key]
    return values


def validate_tool_configuration(document: Mapping[str, object]) -> list[str]:
    """Return structural errors for the canonical django-angular3 tool config."""
    errors: list[str] = []
    errors.extend(validate_ng_openapi_gen_configuration(document))
    drf_spectacular = _required_mapping(document, "drfSpectacular", errors)
    angular = _required_mapping(document, "angular", errors)
    tool = _required_mapping(document, "tool", errors)

    _required_mapping(drf_spectacular, "settings", errors, prefix="drfSpectacular")

    workspace = _required_mapping(angular, "workspace", errors, prefix="angular")
    application = _required_mapping(angular, "application", errors, prefix="angular")
    build = _required_mapping(angular, "build", errors, prefix="angular")
    _require_string(workspace, "packageManager", "angular.workspace", errors)
    _require_string(workspace, "style", "angular.workspace", errors)
    _require_bool(workspace, "routing", "angular.workspace", errors)
    _require_bool(application, "ssr", "angular.application", errors)
    _require_bool(application, "zoneless", "angular.application", errors)
    _require_string(build, "configuration", "angular.build", errors)

    executables = _optional_mapping(tool, "executables")
    for key in ("node", "pnpm", "ng"):
        if key in executables:
            _require_string(executables, key, "tool.executables", errors)
    allowlist = tool.get("commandAllowlist")
    if not isinstance(allowlist, Sequence) or isinstance(allowlist, str):
        errors.append("tool.commandAllowlist must be a sequence of strings.")
    elif not all(isinstance(command, str) and command.strip() for command in allowlist):
        errors.append("tool.commandAllowlist must contain only non-empty strings.")
    _require_string(tool, "ngAddPackage", "tool", errors)
    return errors


def _required_mapping(
    document: Mapping[str, object],
    key: str,
    errors: list[str],
    *,
    prefix: str = "",
) -> Mapping[str, object]:
    value = document.get(key)
    label = f"{prefix}.{key}" if prefix else key
    if not isinstance(value, Mapping):
        errors.append(f"{label} must be a mapping.")
        return {}
    return value


def _require_string(
    document: Mapping[str, object], key: str, section: str, errors: list[str]
) -> None:
    value = document.get(key)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{section}.{key} must be a non-empty string.")


def _require_bool(
    document: Mapping[str, object], key: str, section: str, errors: list[str]
) -> None:
    if not isinstance(document.get(key), bool):
        errors.append(f"{section}.{key} must be a boolean.")


def _optional_mapping(document: Mapping[str, object], key: str) -> Mapping[str, object]:
    value = document.get(key, {})
    if not isinstance(value, Mapping):
        raise AngularCommandError(
            f"django-angular3 configuration section '{key}' must be a mapping."
        )
    return value


def load_ng_openapi_gen_settings(
    config_path: str | Path | None = None,
) -> dict[str, object]:
    """Load global ng-openapi-gen settings from django-angular3.json."""
    path = Path(config_path or DEFAULT_ANGULAR_SETTINGS["config_path"])
    if not path.is_file():
        return {}
    try:
        document = load_document(path)
    except DocumentError as exc:
        raise AngularCommandError(str(exc)) from exc
    if not isinstance(document, Mapping):
        raise AngularCommandError(
            "django-angular3 tool configuration must be a mapping."
        )
    errors = validate_ng_openapi_gen_configuration(document)
    if errors:
        raise AngularCommandError(
            "Invalid ng-openapi-gen configuration: " + "; ".join(errors)
        )
    settings = _required_mapping(document, "ngOpenApiGen", [])
    return dict(settings)


def validate_ng_openapi_gen_configuration(
    document: Mapping[str, object],
) -> list[str]:
    """Return structural errors for the global ng-openapi-gen configuration."""
    errors: list[str] = []
    generator = _required_mapping(document, "ngOpenApiGen", errors)
    _require_string(generator, "serviceSuffix", "ngOpenApiGen", errors)
    _require_bool(generator, "modelIndex", "ngOpenApiGen", errors)

    forbidden = {"$schema", "input", "output"} & set(generator)
    if forbidden:
        labels = ", ".join(sorted(forbidden))
        errors.append(f"ngOpenApiGen must not define per-run setting(s): {labels}.")
    return errors


def load_drf_spectacular_settings(
    config_path: str | Path | None = None,
) -> dict[str, object]:
    """Load global drf-spectacular settings from django-angular3.json."""
    path = Path(config_path or DEFAULT_ANGULAR_SETTINGS["config_path"])
    if not path.is_file():
        return {}
    try:
        document = load_document(path)
    except DocumentError as exc:
        raise AngularCommandError(str(exc)) from exc
    if not isinstance(document, Mapping):
        raise AngularCommandError(
            "django-angular3 tool configuration must be a mapping."
        )
    errors = validate_drf_spectacular_configuration(document)
    if errors:
        raise AngularCommandError(
            "Invalid drf-spectacular configuration: " + "; ".join(errors)
        )
    spectacular = _required_mapping(document, "drfSpectacular", [])
    return dict(_required_mapping(spectacular, "settings", []))


def validate_drf_spectacular_configuration(document: Mapping[str, object]) -> list[str]:
    """Return structural errors for the drf-spectacular tool configuration."""
    errors: list[str] = []
    spectacular = _required_mapping(document, "drfSpectacular", errors)
    _required_mapping(spectacular, "settings", errors, prefix="drfSpectacular")
    return errors


@contextmanager
def use_drf_spectacular_settings(
    derived_settings: Mapping[str, object],
) -> Generator[None, None, None]:
    """Apply derived settings only while invoking drf-spectacular's command."""
    from django.conf import settings as django_settings
    from drf_spectacular.settings import spectacular_settings

    had_original_settings = hasattr(django_settings, "SPECTACULAR_SETTINGS")
    original_settings = getattr(django_settings, "SPECTACULAR_SETTINGS", None)
    django_settings.SPECTACULAR_SETTINGS = dict(derived_settings)
    spectacular_settings.reload()
    try:
        yield
    finally:
        if had_original_settings:
            django_settings.SPECTACULAR_SETTINGS = original_settings
        else:
            delattr(django_settings, "SPECTACULAR_SETTINGS")
        spectacular_settings.reload()


def _normalize_command_allowlist(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        commands = (value,)
    elif isinstance(value, Sequence):
        commands = tuple(value)
    else:
        raise AngularCommandError(
            "command_allowlist must be a string or a sequence of strings."
        )

    normalized_commands: list[str] = []
    for command in commands:
        if not isinstance(command, str):
            raise AngularCommandError("command_allowlist must only contain strings.")

        normalized_command = command.strip().lower()
        if not normalized_command:
            raise AngularCommandError(
                "command_allowlist cannot contain empty command names."
            )

        if normalized_command not in normalized_commands:
            normalized_commands.append(normalized_command)

    return tuple(normalized_commands)
