from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import tools
from .config import ProjectConfig, load_project_config
from .settings import (
    AngularCommandError,
    DjangoAngularSettings,
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
) -> tuple[ProjectConfig, DjangoAngularSettings, list[AngularInvocation]]:
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
    settings: DjangoAngularSettings | None = None,
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
    invocations: list[AngularInvocation], settings: DjangoAngularSettings | None = None
) -> None:
    """Run resolved Angular invocations through the generic tool executor."""
    active_settings = settings or load_angular_settings()
    for invocation in invocations:
        try:
            tools.ensure_command_is_allowed(
                invocation.command_name,
                active_settings.command_allowlist,
            )
            tools.execute_command(invocation.argv, cwd=invocation.cwd)
        except tools.ToolExecutionError as exc:
            raise AngularCommandError(str(exc)) from exc


def build_ng_new_invocations(
    config: ProjectConfig, settings: DjangoAngularSettings, **_: Any
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
    config: ProjectConfig, settings: DjangoAngularSettings, **_: Any
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
    config: ProjectConfig, settings: DjangoAngularSettings, **_: Any
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
    config: ProjectConfig, settings: DjangoAngularSettings, **_: Any
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
    settings: DjangoAngularSettings,
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
    settings: DjangoAngularSettings,
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
    config: ProjectConfig, settings: DjangoAngularSettings, **_: Any
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


def build_ng_openapi_setup_invocations(
    config: ProjectConfig,
    settings: DjangoAngularSettings,
    *,
    output_path: str = "src/app/api",
    helpers_path: str | None = None,
    skip_helpers: bool = False,
    skip_tests: bool = False,
    **_: Any,
) -> list[AngularInvocation]:
    """Bootstrap ng-openapi-gen and Django integration helpers via the ngdj
    ``openapi-setup`` schematic."""
    argv = [
        settings.ng_executable,
        "generate",
        "angular-django2:openapi-setup",
        f"--openapi_spec_file={config.openapi_schema}",
        f"--outputPath={output_path}",
    ]
    if helpers_path:
        argv.append(f"--helpersPath={helpers_path}")
    if skip_helpers:
        argv.append("--skipHelpers=true")
    if skip_tests:
        argv.append("--skipTests=true")

    return [
        AngularInvocation(
            command_name="ng_openapi_setup",
            argv=tuple(argv),
            cwd=config.angular_workspace,
        )
    ]


def build_ng_data_service_invocations(
    config: ProjectConfig,
    settings: DjangoAngularSettings,
    *,
    resource: str,
    project: str | None = None,
    **_: Any,
) -> list[AngularInvocation]:
    """Generate a typed data-service wrapper for a resource via the ngdj
    ``data-service`` schematic."""
    target_project = project or config.project_name
    return [
        AngularInvocation(
            command_name="ng_data_service",
            argv=(
                settings.ng_executable,
                "generate",
                "angular-django2:data-service",
                resource,
                f"--project={target_project}",
            ),
            cwd=config.angular_workspace,
        )
    ]


def build_ng_material_setup_invocations(
    config: ProjectConfig,
    settings: DjangoAngularSettings,
    *,
    project: str | None = None,
    theme: str | None = None,
    typography: bool | None = None,
    animations: bool | None = None,
    **_: Any,
) -> list[AngularInvocation]:
    """Configure Angular Material in an existing project via the ngdj
    ``material-setup`` schematic. Unset options fall back to schematic
    defaults (``theme=indigo-pink``, ``typography=true``, ``animations=true``).
    """
    target_project = project or config.project_name
    argv = [
        settings.ng_executable,
        "generate",
        "angular-django2:material-setup",
        f"--project={target_project}",
    ]
    if theme is not None:
        argv.append(f"--theme={theme}")
    if typography is not None:
        argv.append(f"--typography={_stringify_bool(typography)}")
    if animations is not None:
        argv.append(f"--animations={_stringify_bool(animations)}")

    return [
        AngularInvocation(
            command_name="ng_material_setup",
            argv=tuple(argv),
            cwd=config.angular_workspace,
        )
    ]


def _write_ng_openapi_gen_config(
    config: ProjectConfig, settings: DjangoAngularSettings
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
    settings: DjangoAngularSettings,
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
    config: ProjectConfig, settings: DjangoAngularSettings, **_: Any
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
    config: ProjectConfig, settings: DjangoAngularSettings, **_: Any
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
    config: ProjectConfig, _settings: DjangoAngularSettings, **_: Any
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
    "ng_openapi_setup": build_ng_openapi_setup_invocations,
    "ng_data_service": build_ng_data_service_invocations,
    "ng_material_setup": build_ng_material_setup_invocations,
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
