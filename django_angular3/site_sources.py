"""The site's own source files: copied into the application project by ``build_app``.

Generated code imports files that a site maintains itself (a route guard, an
authentication service). ``artifacts.angularSiteSources`` of the project configuration
names a directory whose tree is copied into ``projects/<project>/src/app/`` of the
workspace, overwriting generated files of the same path. ``build_app`` applies it as a
step after the last generating step and before the terminal build.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Final

from .command_translation import AppBuildStep
from .config import ProjectConfig

#: The command of the copy step; it is run by ``step_execution`` without a subprocess.
SITE_SOURCES_COMMAND: Final = "copy_site_sources"
SITE_SOURCES_STEP: Final = "site-sources"
#: Between the last generating level (10) and the terminal gate (12).
SITE_SOURCES_ORDER: Final = 11
_TARGET: Final = "artifacts.angularSiteSources"


class SiteSourcesError(ValueError):
    """The site sources cannot be used or copied; the message names the cause."""


def site_sources_destination(project_config: ProjectConfig) -> Path:
    """``projects/<project>/src/app`` of the workspace."""
    return (
        project_config.angular_workspace
        / "projects"
        / project_config.project_name
        / "src"
        / "app"
    )


def validate_site_sources(project_config: ProjectConfig) -> None:
    """Fail clearly when the configured directory is missing or holds no files."""
    source = project_config.angular_site_sources
    if source is None:
        return
    if not source.is_dir():
        raise SiteSourcesError(
            f"artifacts.angularSiteSources {source} is not a directory."
        )
    if not any(path.is_file() for path in source.rglob("*")):
        raise SiteSourcesError(f"artifacts.angularSiteSources {source} holds no files.")


def with_site_sources_step(
    steps: tuple[AppBuildStep, ...], project_config: ProjectConfig
) -> tuple[AppBuildStep, ...]:
    """Insert the copy step before the terminal gate; ``steps`` unchanged without a key.

    Validation runs first, so a bad directory fails before any step runs. With no steps
    (nothing changed) there is no terminal gate and nothing to copy for.
    """
    source = project_config.angular_site_sources
    if source is None or not steps:
        return steps
    validate_site_sources(project_config)
    destination = site_sources_destination(project_config)
    step = AppBuildStep(
        name_id=SITE_SOURCES_STEP,
        exec_order=SITE_SOURCES_ORDER,
        change_op="copy",
        change_reason=(
            "Copy the site's own source files into the application project before "
            "the terminal build."
        ),
        change_target=_TARGET,
        change_domain=None,
        command=SITE_SOURCES_COMMAND,
        parameters={"source": str(source), "destination": str(destination)},
    )
    index = next(
        (i for i, s in enumerate(steps) if s.name_id == "last-check"), len(steps)
    )
    return (*steps[:index], step, *steps[index:])


def copy_site_sources(project_config: ProjectConfig) -> list[str]:
    """Copy the tree into the application project; returns the copied relative paths."""
    validate_site_sources(project_config)
    source = project_config.angular_site_sources
    assert source is not None
    destination = site_sources_destination(project_config)
    copied: list[str] = []
    try:
        for path in sorted(source.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(source)
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
            copied.append(relative.as_posix())
    except OSError as exc:
        raise SiteSourcesError(
            f"Cannot copy the site sources {source} to {destination}: {exc}"
        ) from exc
    return copied
