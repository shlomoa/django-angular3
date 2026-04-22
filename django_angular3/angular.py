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


def plan_angular_init(
    project_name: str, *, folder: str | None = None, package_manager: str | None = None
) -> list[AngularInvocation]:
    settings = load_angular_settings()
    target_folder = folder or project_name
    workspace_dir = _resolve_workspace_dir(target_folder)
    workspace_package_manager = package_manager or "pnpm"

    return [
        AngularInvocation(
            argv=(
                settings.ng_executable,
                "new",
                project_name,
                "--defaults",
                "--skip-git",
                "--skip-install",
                "--no-create-application",
                f"--package-manager={workspace_package_manager}",
                f"--directory={target_folder}",
            ),
            cwd=Path.cwd(),
        ),
        *_build_workspace_configuration_invocations(
            workspace_dir, settings, package_manager=workspace_package_manager
        ),
    ]


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
    return _build_workspace_configuration_invocations(
        config.angular_output, settings, package_manager=settings.package_manager
    )


def _build_workspace_configuration_invocations(
    workspace_dir: Path, settings: AngularSettings, *, package_manager: str
) -> list[AngularInvocation]:
    return [
        AngularInvocation(
            argv=(
                settings.ng_executable,
                "config",
                "cli.packageManager",
                package_manager,
            ),
            cwd=workspace_dir,
        ),
        AngularInvocation(
            argv=(
                settings.ng_executable,
                "config",
                "schematics.@schematics/angular:application.style",
                settings.style,
            ),
            cwd=workspace_dir,
        ),
        AngularInvocation(
            argv=(
                settings.ng_executable,
                "config",
                "schematics.@schematics/angular:application.routing",
                _stringify_bool(settings.routing),
            ),
            cwd=workspace_dir,
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
_COMMAND_BUILDERS = {
    "ng_new": build_ng_new_invocations,
    "ng_config": build_ng_config_invocations,
    "ng_build": build_ng_build_invocations,
    "ng_gen_app": build_ng_gen_app_invocations,
    "ng_openapi_gen": build_ng_openapi_gen_invocations,
}


def _stringify_bool(value: bool) -> str:
    return "true" if value else "false"


def _resolve_workspace_dir(folder: str) -> Path:
    workspace_dir = Path(folder)
    if workspace_dir.is_absolute():
        return workspace_dir.resolve()
    return (Path.cwd() / workspace_dir).resolve()
