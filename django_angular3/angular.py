from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import ProjectConfig, load_project_config
from .settings import AngularCommandError, AngularSettings, load_angular_settings


@dataclass(frozen=True)
class AngularInvocation:
    """A single Angular CLI invocation and the directory it should run from."""

    command_name: str
    argv: tuple[str, ...]
    cwd: Path

    def to_dict(self) -> dict[str, object]:
        return {"argv": list(self.argv), "cwd": str(self.cwd)}


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


def execute_invocations(
    invocations: list[AngularInvocation], settings: AngularSettings | None = None
) -> None:
    active_settings = settings or load_angular_settings()
    for invocation in invocations:
        _ensure_command_is_allowed(invocation.command_name, active_settings)
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
            command_name="ng_new",
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
            command_name="ng_config",
            argv=(
                settings.ng_executable,
                "config",
                "cli.packageManager",
                settings.package_manager,
            ),
            cwd=config.angular_output,
        ),
        AngularInvocation(
            command_name="ng_config",
            argv=(
                settings.ng_executable,
                "config",
                "schematics.@schematics/angular:application.style",
                settings.style,
            ),
            cwd=config.angular_output,
        ),
        AngularInvocation(
            command_name="ng_config",
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
            command_name="ng_build",
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
            command_name="ng_gen_app",
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
            command_name="ng_openapi_gen",
            argv=(
                settings.pnpm_executable,
                "exec",
                "ng-openapi-gen",
                source_flag,
                str(source),
            ),
            cwd=config.angular_output,
        )
    ]


def build_ng_add_invocations(
    config: ProjectConfig, settings: AngularSettings, *, package: str = "angular-django2", **_: Any
) -> list[AngularInvocation]:
    return [
        AngularInvocation(
            command_name="ng_add",
            argv=(
                settings.ng_executable,
                "add",
                package,
                "--skip-confirmation",
            ),
            cwd=config.angular_output,
        )
    ]


_COMMAND_BUILDERS = {
    "ng_new": build_ng_new_invocations,
    "ng_config": build_ng_config_invocations,
    "ng_build": build_ng_build_invocations,
    "ng_gen_app": build_ng_gen_app_invocations,
    "ng_openapi_gen": build_ng_openapi_gen_invocations,
    "ng_add": build_ng_add_invocations,
}


def _stringify_bool(value: bool) -> str:
    return "true" if value else "false"


def _ensure_command_is_allowed(command_name: str, settings: AngularSettings) -> None:
    normalized_command_name = command_name.strip().lower()
    if normalized_command_name in settings.command_allowlist:
        return

    allowed_commands = ", ".join(settings.command_allowlist) or "<none>"
    raise AngularCommandError(
        f"Command '{command_name}' is not allowed. Allowed commands: {allowed_commands}."
    )
