from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .config import ProjectConfig, load_project_config


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


@dataclass(frozen=True)
class AngularInvocation:
    """A single Angular CLI invocation and the directory it should run from."""

    argv: tuple[str, ...]
    cwd: Path

    def to_dict(self) -> dict[str, object]:
        return {"argv": list(self.argv), "cwd": str(self.cwd)}


def load_angular_settings(overrides: Mapping[str, Any] | None = None) -> AngularSettings:
    data = dict(_load_django_settings())
    if overrides:
        data.update(overrides)
    return AngularSettings(**data)


def plan_angular_command(
    command_name: str, config_path: str | Path | None = None, **options: Any
) -> list[AngularInvocation]:
    settings = load_angular_settings()
    config = load_project_config(config_path or settings.config_path)

    builder = _COMMAND_BUILDERS.get(command_name)
    if builder is None:
        raise AngularCommandError(f"Unknown Angular command '{command_name}'.")

    return builder(config, settings, **options)


def format_invocations(invocations: list[AngularInvocation]) -> str:
    return json.dumps([invocation.to_dict() for invocation in invocations], indent=2)


def execute_invocations(invocations: list[AngularInvocation]) -> None:
    for invocation in invocations:
        try:
            subprocess.run(invocation.argv, cwd=invocation.cwd, check=True)
        except FileNotFoundError as exc:
            raise AngularCommandError(f"Command not found: {invocation.argv[0]}") from exc
        except subprocess.CalledProcessError as exc:
            raise AngularCommandError(
                f"Command '{' '.join(invocation.argv)}' failed with exit code {exc.returncode}."
            ) from exc


def build_ng_new_invocations(
    config: ProjectConfig, settings: AngularSettings, **_: Any
) -> list[AngularInvocation]:
    return [
        AngularInvocation(
            argv=(
                settings.ng_executable,
                "new",
                config.project_name,
                "--defaults",
                "--skip-git",
                "--skip-install",
                "--no-create-application",
                f"--package-manager={settings.package_manager}",
                f"--directory={config.angular_output}",
            ),
            cwd=config.angular_output.parent,
        )
    ]


def build_ng_config_invocations(
    config: ProjectConfig, settings: AngularSettings, **_: Any
) -> list[AngularInvocation]:
    return [
        AngularInvocation(
            argv=(
                settings.ng_executable,
                "config",
                "cli.packageManager",
                settings.package_manager,
            ),
            cwd=config.angular_output,
        ),
        AngularInvocation(
            argv=(
                settings.ng_executable,
                "config",
                "schematics.@schematics/angular:application.style",
                settings.style,
            ),
            cwd=config.angular_output,
        ),
        AngularInvocation(
            argv=(
                settings.ng_executable,
                "config",
                "schematics.@schematics/angular:application.routing",
                _stringify_bool(settings.routing),
            ),
            cwd=config.angular_output,
        ),
    ]


def build_ng_build_invocations(
    config: ProjectConfig, settings: AngularSettings, **_: Any
) -> list[AngularInvocation]:
    return [
        AngularInvocation(
            argv=(
                settings.ng_executable,
                "build",
                config.project_name,
                f"--configuration={settings.build_configuration}",
            ),
            cwd=config.angular_output,
        )
    ]


def build_ng_gen_app_invocations(
    config: ProjectConfig, settings: AngularSettings, *, app_name: str | None = None, **_: Any
) -> list[AngularInvocation]:
    target_app = app_name or config.project_name
    return [
        AngularInvocation(
            argv=(
                settings.ng_executable,
                "generate",
                "application",
                target_app,
                f"--style={settings.style}",
                "--routing" if settings.routing else "--no-routing",
            ),
            cwd=config.angular_output,
        )
    ]


def build_ng_openapi_gen_invocations(
    config: ProjectConfig, settings: AngularSettings, **_: Any
) -> list[AngularInvocation]:
    source = config.ng_openapi_gen_config or config.openapi_source
    source_flag = "-c" if config.ng_openapi_gen_config else "-i"
    return [
        AngularInvocation(
            argv=(settings.npx_executable, "ng-openapi-gen", source_flag, str(source)),
            cwd=config.angular_output,
        )
    ]


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


_COMMAND_BUILDERS = {
    "ng_new": build_ng_new_invocations,
    "ng_config": build_ng_config_invocations,
    "ng_build": build_ng_build_invocations,
    "ng_gen_app": build_ng_gen_app_invocations,
    "ng_openapi_gen": build_ng_openapi_gen_invocations,
}


def _stringify_bool(value: bool) -> str:
    return "true" if value else "false"
