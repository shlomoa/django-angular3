from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import ProjectConfig, load_project_config
from .settings import (
    AngularCommandError,
    AngularSettings,
    load_angular_settings,
    load_ng_openapi_gen_settings,
)


@dataclass(frozen=True)
class AngularInvocation:
    """A single Angular CLI invocation and the directory it should run from."""

    command_name: str
    argv: tuple[str, ...]
    cwd: Path

    def to_dict(self) -> dict[str, object]:
        return {"argv": list(self.argv), "cwd": str(self.cwd)}


AngularInvocationBuilder = Callable[..., list[AngularInvocation]]


def resolve_angular_command(
    command_name: str, **options: Any
) -> list[AngularInvocation]:
    """Resolve one logical djng command into an ordered list of subprocess calls.

    This function does not execute Angular or Node tooling. It loads the
    project configuration and Angular settings, chooses the matching command
    builder, and returns the concrete ``AngularInvocation`` list that a dry run
    can print or ``execute_invocations`` can later run.
    """
    _, _, invocations = resolve_angular_command_context(command_name, **options)
    return invocations


def resolve_angular_command_context(
    command_name: str, **options: Any
) -> tuple[ProjectConfig, AngularSettings, list[AngularInvocation]]:
    """Resolve a command with its discovered project and derived tool settings."""
    settings = load_angular_settings()
    config = load_project_config()

    builder = _COMMAND_BUILDERS.get(command_name)
    if builder is None:
        raise AngularCommandError(f"Unknown Angular command '{command_name}'.")

    return config, settings, builder(config, settings, **options)


def format_invocations(
    invocations: list[AngularInvocation],
    config: ProjectConfig | None = None,
    settings: AngularSettings | None = None,
) -> str:
    """Serialize dry-run configuration, derived paths, and subprocess calls."""
    serialized_invocations = [invocation.to_dict() for invocation in invocations]
    if config is None or settings is None:
        return json.dumps(serialized_invocations, indent=2)

    return json.dumps(
        {
            "projectConfig": str(config.config_path),
            "toolConfig": settings.config_path,
            "derivedPaths": {
                "openapiSchema": str(config.openapi_schema),
                "openuiSpecification": str(config.openui_specification),
                "angularWorkspace": str(config.angular_workspace),
            },
            "invocations": serialized_invocations,
        },
        indent=2,
    )


def execute_invocations(
    invocations: list[AngularInvocation], settings: AngularSettings | None = None
) -> None:
    """Run a previously resolved ordered list of subprocess calls."""
    active_settings = settings or load_angular_settings()
    for invocation in invocations:
        _ensure_command_is_allowed(invocation.command_name, active_settings)
        try:
            subprocess.run(invocation.argv, cwd=invocation.cwd, check=True)
        except FileNotFoundError as exc:
            raise AngularCommandError(
                f"Command not found: {invocation.argv[0]}"
            ) from exc
        except subprocess.CalledProcessError as exc:
            raise AngularCommandError(
                f"Command '{' '.join(invocation.argv)}' failed with exit code "
                f"{exc.returncode}."
            ) from exc


def build_ng_new_invocations(
    config: ProjectConfig, settings: AngularSettings, **_: Any
) -> list[AngularInvocation]:
    # Ensure the parent directory exists before calling subprocess.run
    config.angular_workspace.parent.mkdir(parents=True, exist_ok=True)
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
                f"--directory={config.angular_workspace.name}",
            ),
            cwd=config.angular_workspace.parent,
        )
    ]


def build_ng_workspace_schematic_invocations(
    config: ProjectConfig, settings: AngularSettings, **_: Any
) -> list[AngularInvocation]:
    return [
        AngularInvocation(
            command_name="ng_workspace",
            argv=(
                settings.ng_executable,
                "generate",
                "angular-django2:workspace-setup",
                config.project_name,
            ),
            cwd=config.angular_workspace,
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
            cwd=config.angular_workspace,
        ),
        AngularInvocation(
            command_name="ng_config",
            argv=(
                settings.ng_executable,
                "config",
                "schematics.@schematics/angular:application.style",
                settings.style,
            ),
            cwd=config.angular_workspace,
        ),
        AngularInvocation(
            command_name="ng_config",
            argv=(
                settings.ng_executable,
                "config",
                "schematics.@schematics/angular:application.routing",
                _stringify_bool(settings.routing),
            ),
            cwd=config.angular_workspace,
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
            cwd=config.angular_workspace,
        )
    ]


def build_ng_gen_app_invocations(
    config: ProjectConfig,
    settings: AngularSettings,
    *,
    app_name: str | None = None,
    **_: Any,
) -> list[AngularInvocation]:
    target_app = app_name or config.project_name
    return [
        AngularInvocation(
            command_name="ng_gen_app",
            argv=(
                settings.ng_executable,
                "generate",
                "angular-django2:material-app",
                target_app,
                f"--style={settings.style}",
                "--routing" if settings.routing else "--no-routing",
                f"--ssr={_stringify_bool(settings.ssr)}",
                f"--zoneless={_stringify_bool(settings.zoneless)}",
                "--defaults",
            ),
            cwd=config.angular_workspace,
        )
    ]


def build_ng_complex_component_invocations(
    config: ProjectConfig,
    settings: AngularSettings,
    *,
    name: str,
    target_path: str,
    features: str | list[str] | tuple[str, ...],
    project: str | None = None,
    mode: str = "create",
    confirm: bool = False,
    **_: Any,
) -> list[AngularInvocation]:
    """Build the ngdj advanced complex-component schematic invocation."""
    _validate_complex_component_options(name, target_path, features, mode, confirm)
    feature_names = _normalize_complex_component_features(features)
    argv = [
        settings.ng_executable,
        "generate",
        "angular-django2:complex-component",
        name,
        f"--path={target_path}",
        f"--features={','.join(feature_names)}",
        f"--mode={mode}",
    ]
    if project:
        argv.append(f"--project={project}")
    if mode == "delete":
        argv.append("--confirm=true")

    return [
        AngularInvocation(
            command_name="ng_complex_component",
            argv=tuple(argv),
            cwd=config.angular_workspace,
        )
    ]


def build_ng_openapi_gen_invocations(
    config: ProjectConfig, settings: AngularSettings, **_: Any
) -> list[AngularInvocation]:
    generated_config_path = _write_ng_openapi_gen_config(config, settings)
    return [
        AngularInvocation(
            command_name="ng_openapi_gen",
            argv=(
                settings.pnpm_executable,
                "exec",
                "ng-openapi-gen",
                "-c",
                str(generated_config_path),
            ),
            cwd=config.angular_workspace,
        )
    ]


def _write_ng_openapi_gen_config(
    config: ProjectConfig, settings: AngularSettings
) -> Path:
    """Write the derived, per-run ng-openapi-gen configuration file."""
    generated_config_path = config.angular_workspace / "ng-openapi-gen.json"
    output_path = config.angular_workspace / "generated" / "ng-openapi-gen"
    document: dict[str, object] = {
        **load_ng_openapi_gen_settings(settings.config_path),
        "$schema": (
            "https://raw.githubusercontent.com/cyclosproject/ng-openapi-gen/"
            "master/ng-openapi-gen-schema.json"
        ),
        "input": str(config.openapi_schema),
        "output": str(output_path),
    }
    generated_config_path.parent.mkdir(parents=True, exist_ok=True)
    generated_config_path.write_text(
        json.dumps(document, indent=2) + "\n", encoding="utf-8"
    )
    return generated_config_path


def build_ng_add_invocations(
    config: ProjectConfig,
    settings: AngularSettings,
    *,
    package: str | None = None,
    **_: Any,
) -> list[AngularInvocation]:
    target_package = package or settings.ng_add_package
    return [
        AngularInvocation(
            command_name="ng_add",
            argv=(
                settings.ng_executable,
                "add",
                target_package,
                "--skip-confirmation",
            ),
            cwd=config.angular_workspace,
        )
    ]


def build_ng_workspace_invocations(
    config: ProjectConfig, settings: AngularSettings, **_: Any
) -> list[AngularInvocation]:
    """Create and bootstrap an Angular workspace with angular-django2 defaults."""
    invocations = _relabel_invocations(
        build_ng_new_invocations(config, settings), "ng_workspace"
    )
    invocations.extend(
        _relabel_invocations(
            build_ng_config_invocations(config, settings), "ng_workspace"
        )
    )
    invocations.extend(
        _relabel_invocations(build_ng_add_invocations(config, settings), "ng_workspace")
    )
    invocations.extend(build_ng_workspace_schematic_invocations(config, settings))
    return invocations


def build_ng_workspace_modify_invocations(
    config: ProjectConfig, settings: AngularSettings, **_: Any
) -> list[AngularInvocation]:
    """Reapply workspace defaults, collection registration, and
    workspace scaffolding."""
    invocations = _relabel_invocations(
        build_ng_config_invocations(config, settings), "ng_workspace_modify"
    )
    invocations.extend(
        _relabel_invocations(
            build_ng_add_invocations(config, settings), "ng_workspace_modify"
        )
    )
    invocations.extend(
        _relabel_invocations(
            build_ng_workspace_schematic_invocations(config, settings),
            "ng_workspace_modify",
        )
    )
    return invocations


def build_ng_workspace_delete_invocations(
    config: ProjectConfig, _settings: AngularSettings, **_: Any
) -> list[AngularInvocation]:
    """Delete the entire workspace folder using Python's native
    cross-platform shutil."""
    import sys

    py_code = (
        "import shutil; shutil.rmtree("
        f"r'{config.angular_workspace}', ignore_errors=True)"
    )

    return [
        AngularInvocation(
            command_name="ng_workspace_delete",
            argv=(sys.executable, "-c", py_code),
            cwd=config.angular_workspace.parent,
        )
    ]


_COMMAND_BUILDERS: dict[str, AngularInvocationBuilder] = {
    "ng_new": build_ng_new_invocations,
    "ng_workspace": build_ng_workspace_invocations,
    "ng_config": build_ng_config_invocations,
    "ng_build": build_ng_build_invocations,
    "ng_gen_app": build_ng_gen_app_invocations,
    "ng_complex_component": build_ng_complex_component_invocations,
    "ng_openapi_gen": build_ng_openapi_gen_invocations,
    "ng_add": build_ng_add_invocations,
    "ng_workspace_modify": build_ng_workspace_modify_invocations,
    "ng_workspace_delete": build_ng_workspace_delete_invocations,
}


def _stringify_bool(value: bool) -> str:
    return "true" if value else "false"


_COMPLEX_COMPONENT_FEATURES = frozenset(
    {"mixins", "nested", "projection", "cdk-overlay"}
)
_COMPLEX_COMPONENT_NAME = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")


def _normalize_complex_component_features(
    features: str | list[str] | tuple[str, ...],
) -> tuple[str, ...]:
    values = features.split(",") if isinstance(features, str) else features
    return tuple(feature.strip() for feature in values if feature.strip())


def _validate_complex_component_options(
    name: str,
    target_path: str,
    features: str | list[str] | tuple[str, ...],
    mode: str,
    confirm: bool,
) -> None:
    if not _COMPLEX_COMPONENT_NAME.fullmatch(name):
        raise AngularCommandError("Complex component name must be kebab-case.")

    path = Path(target_path)
    if path.is_absolute() or ".." in path.parts or not target_path.strip():
        raise AngularCommandError(
            "Complex component path must be a non-empty relative path within the "
            "Angular application source tree."
        )

    feature_names = _normalize_complex_component_features(features)
    invalid_features = set(feature_names) - _COMPLEX_COMPONENT_FEATURES
    if (
        not feature_names
        or invalid_features
        or len(set(feature_names)) != len(feature_names)
    ):
        supported = ", ".join(sorted(_COMPLEX_COMPONENT_FEATURES))
        raise AngularCommandError(
            "Complex component features must be a non-empty, unique subset of: "
            f"{supported}."
        )

    if mode not in {"create", "modify", "delete"}:
        raise AngularCommandError(
            "Complex component mode must be create, modify, or delete."
        )
    if mode == "delete" and not confirm:
        raise AngularCommandError("Complex component deletion requires --confirm.")


def _relabel_invocations(
    invocations: list[AngularInvocation], command_name: str
) -> list[AngularInvocation]:
    return [
        AngularInvocation(
            command_name=command_name,
            argv=invocation.argv,
            cwd=invocation.cwd,
        )
        for invocation in invocations
    ]


def _ensure_command_is_allowed(command_name: str, settings: AngularSettings) -> None:
    normalized_command_name = command_name.strip().lower()
    if normalized_command_name in settings.command_allowlist:
        return

    allowed_commands = ", ".join(settings.command_allowlist) or "<none>"
    raise AngularCommandError(
        f"Command '{command_name}' is not allowed. Allowed commands: "
        f"{allowed_commands}."
    )
