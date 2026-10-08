"""
Django Angular3 Management Command: Build App

This module implements the build_app management command for building the
Django Angular3 application.
"""

import argparse
import logging
from pathlib import Path
from typing import Any

from bin.openui_spec import (  # type: ignore[import-untyped]
    OpenUiJson,
    OpenUiJsonError,
)
from django.core.management.base import BaseCommand, CommandError

from django_angular3.changes import Change, ChangeDomain, ChangeDomainResult, ChangeSet
from django_angular3.command_translation import (
    AppBuildStep,
    CommandTranslationError,
    translate_changes,
)
from django_angular3.config import ProjectConfig
from django_angular3.config_changes import compare_project_config
from django_angular3.external_comparisons import (
    ExternalComparisonError,
    compare_openui_files,
)
from django_angular3.ngdj_command_mapping import (
    CommandMapping,
    CommandMappingError,
    load_command_mapping,
)
from django_angular3.openapi_changes import (
    OpenApiComparisonError,
    compare_openapi_files,
)
from django_angular3.settings import (
    AngularCommandError,
    DjangoAngularSettings,
    load_angular_settings,
)
from django_angular3.step_bridge import StepBridgeError, resolve_steps
from django_angular3.step_execution import (
    EVIDENCE_FILE_NAME,
    ExecutionEvidence,
    execute_steps,
    new_evidence,
    unresolved_steps,
    write_evidence,
)

from ...config import ConfigError, load_project_config

logger = logging.getLogger(__name__)


class OpenAPIConfiguration:
    """
    Responsible for managing the OpenAPI configuration.
    """

    def __init__(self, openapi_path: Path):
        self._openapi_path = openapi_path

    @property
    def openapi_path(self) -> Path:
        """Return the OpenAPI schema path."""
        return self._openapi_path

    def load(self):
        """
        Load the OpenAPI schema from the specified path.
        Raises ConfigError if loading fails.
        """
        try:
            raise NotImplementedError("Loading OpenAPI schema is not implemented.")
        except ConfigError as e:
            raise CommandError(f"Failed to load OpenAPI schema: {e}") from e


class OpenUIConfiguration:
    """
    Responsible for managing the OpenUI configuration.
    """

    def __init__(self, openui_path: Path):
        self.openui_path: Path = openui_path
        self.openui_spec: dict[str, Any] | None = None

    def load(self):
        """
        Load the OpenUI specification from the specified path.
        Raises CommandError if loading fails.
        """
        try:
            self.openui_spec = OpenUiJson.load(self.openui_path).document
        except OpenUiJsonError as exc:
            raise CommandError(f"Failed to load OpenUI specification: {exc}") from exc


class Configuration:
    """
    Docstring for Configurations

    Configuration class responsible for:
    * Loading project configuration from specified paths or default locations.
    * Managing OpenAPI configuration using the OpenAPIConfiguration class
    * Managing OpenUI configuration using the OpenUIConfiguration class
    * Managing project configuration using the ProjectConfiguration class

    var input: paths to project configuration file.
    var output: loaded configuration objects for each type.
    """

    def __init__(self, project_config_path: str | Path | None = None):
        self._project_config_path: str | Path | None = project_config_path
        self._openapi_config: OpenAPIConfiguration | None = None
        self._openui_config: OpenUIConfiguration | None = None
        self._load()

    def _load(self):
        """
        Docstring for load

        :param self: Description
        """
        logger.debug("Loading project configuration from %s", self._project_config_path)
        self._project_config: ProjectConfig = load_project_config(
            self._project_config_path
        )
        logger.debug("OpenAPI schema: %s", self._project_config.openapi_schema)
        self._openapi_config = OpenAPIConfiguration(self._project_config.openapi_schema)
        logger.debug(
            "OpenUI specification: %s", self._project_config.openui_specification
        )
        self._openui_config = OpenUIConfiguration(
            self._project_config.openui_specification
        )

    @property
    def openapi_config(self) -> OpenAPIConfiguration | None:
        """Return the loaded OpenAPI configuration."""
        return self._openapi_config

    @property
    def openui_config(self) -> OpenUIConfiguration | None:
        """Return the loaded OpenUI configuration."""
        return self._openui_config

    @property
    def project_config(self) -> ProjectConfig:
        """Return the loaded project configuration."""
        return self._project_config


class ChangeDetector:
    """

    ChangeDetector class responsible for:
    * Comparing current and previous configurations to detect changes.
    * Determining the type of change (add, remove, modify, no-change).
    * Identifying affected resources based on the detected changes.
    """

    def __init__(
        self,
        current_config: Configuration,
        previous_config: Configuration,
    ):
        self._current_config: Configuration = current_config
        self._previous_config: Configuration = previous_config

    def _diff_openui_specifications(self) -> tuple[Change, ...]:
        current_openui = self._current_config.openui_config
        previous_openui = self._previous_config.openui_config
        if current_openui is None or previous_openui is None:
            raise CommandError("OpenUI configurations must be loaded before diffing.")
        try:
            return compare_openui_files(
                previous_openui.openui_path,
                current_openui.openui_path,
            )
        except (ExternalComparisonError, OSError) as exc:
            raise CommandError(f"Failed to diff OpenUI specifications: {exc}") from exc

    def _diff_openapi_schemas(self) -> tuple[Change, ...]:
        current_openapi = self._current_config.openapi_config
        previous_openapi = self._previous_config.openapi_config
        if current_openapi is None or previous_openapi is None:
            raise CommandError("OpenAPI configurations must be loaded before diffing.")
        try:
            return compare_openapi_files(
                previous_openapi.openapi_path,
                current_openapi.openapi_path,
            )
        except (ExternalComparisonError, OpenApiComparisonError, OSError) as exc:
            raise CommandError(f"Failed to diff OpenAPI schemas: {exc}") from exc

    def detect_changes(self) -> ChangeSet:
        """Derive the canonical ChangeSet for the current configuration pair."""
        logger.debug("Detecting changes between previous and current configuration")
        try:
            project_changes = compare_project_config(
                self._previous_config.project_config,
                self._current_config.project_config,
            )
            openapi_changes = self._diff_openapi_schemas()
            openui_changes = self._diff_openui_specifications()
        except (ExternalComparisonError, OpenApiComparisonError, OSError) as exc:
            raise CommandError(f"Failed to detect changes: {exc}") from exc

        logger.debug(
            "Detected changes: project=%d openapi=%d openui=%d",
            len(project_changes),
            len(openapi_changes),
            len(openui_changes),
        )

        return ChangeSet(
            baseline={
                "projectConfig": str(self._previous_config.project_config.config_path)
            },
            candidate={
                "projectConfig": str(self._current_config.project_config.config_path)
            },
            domains={
                ChangeDomain.STATIC_CONFIG: ChangeDomainResult(
                    ChangeDomain.STATIC_CONFIG
                ),
                ChangeDomain.PROJECT_CONFIG: ChangeDomainResult(
                    ChangeDomain.PROJECT_CONFIG, project_changes
                ),
                ChangeDomain.OPENAPI: ChangeDomainResult(
                    ChangeDomain.OPENAPI, openapi_changes
                ),
                ChangeDomain.OPENUI: ChangeDomainResult(
                    ChangeDomain.OPENUI, openui_changes
                ),
            },
        )


def load_ngdj_mapping(
    change_set: ChangeSet, project_config: ProjectConfig
) -> CommandMapping | None:
    """Load the ngdj command mapping when a Change needs it.

    OpenUI and OpenAPI Changes are translated with the mapping that the Angular
    workspace's installed ``angular-django2`` package ships. Other Changes need none,
    so deriving their steps does not require the package to be installed.
    """
    needs_mapping = any(
        change_set.domains[domain].changes
        for domain in (ChangeDomain.OPENUI, ChangeDomain.OPENAPI)
    )
    if not needs_mapping:
        return None
    try:
        return load_command_mapping(
            project_config.angular_workspace, load_angular_settings().ng_add_package
        )
    except CommandMappingError as exc:
        raise CommandError(
            f"Cannot derive the steps for the OpenUI and OpenAPI changes: {exc}"
        ) from exc


class ChangeExecution:
    """
    Docstring for ChangeExecution

    ChangeExecution class responsible for:
    * Executing changes based on the detected differences.
    * Managing the order of execution and handling dependencies.
    * Rolling back changes in case of failures.
    """

    def _translate_change_set(
        self, change_set: ChangeSet, mapping: CommandMapping | None = None
    ) -> tuple[AppBuildStep, ...]:
        """Translate the ChangeSet into the ordered steps."""
        changes = tuple(
            change
            for domain in ChangeDomain
            for change in change_set.domains[domain].changes
        )
        logger.debug("Translating %d changes into commands", len(changes))
        try:
            return translate_changes(changes, mapping)
        except CommandTranslationError as exc:
            raise CommandError(f"Failed to translate changes: {exc}") from exc

    def execute(
        self,
        change_set: ChangeSet,
        project_config: ProjectConfig,
        output_path: str,
        dry_run: bool,
        force: bool,
        mapping: CommandMapping | None = None,
        settings: DjangoAngularSettings | None = None,
    ) -> ExecutionEvidence:
        """
        Derive the steps of the changes and, unless ``dry_run``, run them.

        The steps are bridged to their wrappers and their parameters are resolved from
        the project configuration and the mapping. A dry run returns them as
        evidence and touches nothing. A real run first refuses steps with an
        unresolved parameter, then runs the steps level by level, halts at the
        first failure, writes the evidence to ``<output_path>/build-evidence.json``
        (also after a failure) and raises ``CommandError`` for the failure.

        ``force`` is not honored yet and is refused rather than ignored.

        Raises CommandError if resolving the steps or running them fails.
        """
        logger.debug("Executing change set")
        if force:
            raise CommandError(
                "--force start-from-scratch is not implemented: change detection "
                "cannot be overridden yet."
            )
        try:
            settings = settings or load_angular_settings()
            steps = resolve_steps(
                self._translate_change_set(change_set, mapping),
                project_config,
                mapping,
            )
        except (StepBridgeError, AngularCommandError, ConfigError) as exc:
            raise CommandError(f"Failed to resolve the steps: {exc}") from exc

        evidence = new_evidence(
            project_config, settings, mapping, steps, dry_run=dry_run
        )
        if dry_run:
            return evidence

        problems = unresolved_steps(steps)
        if problems:
            raise CommandError(
                "Cannot run the steps; nothing was executed: "
                + "; ".join(problems)
                + "."
            )
        execute_steps(evidence, project_config, settings)
        evidence_path = write_evidence(evidence, Path(output_path))
        failed = evidence.failed
        if failed is not None:
            raise CommandError(
                f"Step {failed.step.name_id} ({failed.step.command}, "
                f"{failed.step.change_target}) failed: {failed.error}\n"
                f"The remaining steps were skipped. Evidence: {evidence_path}"
            )
        return evidence


class Command(BaseCommand):
    """
    Command class responsible for:
    * Parsing command-line arguments.
    * Coordinating the build process.
    * Handling change detection and execution.
    """

    help = "Build the application frontend as described by the configuration files."

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--current-config",
            type=str,
            help="Path to current configuration: \n"
            "The user is responsible for providing it.\n"
            "The default is calculated from Django as follows:\n"
            "- located at the root folder\n"
            "- project_name calculated from Django\n"
            "- file name is django-angular3-<project_name>.json",
        )
        parser.add_argument(
            "--previous-config",
            type=str,
            help="Path to previous configuration: \n"
            "If not provided, path name will be the same as the current\n"
            "with .json replaced by .previous.json.\n"
            "if none existing, it will be treated as a start-from-scratch build.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print the ordered steps, their commands, parameters and reasons "
            "without running them or changing the workspace",
        )
        parser.add_argument(
            "--output",
            default="build",
            help="Directory to write the evidence of a run (build-evidence.json).",
        )
        parser.add_argument(
            "--force",
            choices=["start-from-scratch"],
            help="Override change detection; treat as start-from-scratch.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """build the missing pieces for a complete Angular implementation
        of the requested changes.

        The build process is a multi-step operation that involves:
        1. Load current and previous configurations.
        2. Compare current with previous configurations and derive a change set.
        3. Translate the change set into a directed graph of steps.
        4. Execute the steps in order, respecting dependencies.

        Configuration management is delegated to a Configuration class - covering
        steps 1 and 2. Change detection and derivation is delegated to
        ChangeDetector class - covering step 3. Change execution is delegated to
        ChangeExecution class - covering step 4.

        Raises:
            CommandError: If the configuration is invalid, its schema source is
                absent, or ``oasdiff`` cannot be prepared or used.
        """
        logger.debug("build_app started with options: %s", options)
        try:
            current_config = Configuration(options["current_config"])
            previous_config = Configuration(options["previous_config"])
            detector = ChangeDetector(current_config, previous_config)
            change_set: ChangeSet = detector.detect_changes()
            mapping = load_ngdj_mapping(change_set, current_config.project_config)
            executor = ChangeExecution()
            evidence = executor.execute(
                change_set,
                current_config.project_config,
                options["output"],
                options["dry_run"],
                options["force"],
                mapping=mapping,
            )
            if options["dry_run"]:
                self.stdout.write(evidence.to_json())
            else:
                self.stdout.write(
                    f"Executed {len(evidence.records)} step(s). Evidence: "
                    f"{Path(options['output']) / EVIDENCE_FILE_NAME}"
                )
        except ConfigError as exc:
            raise CommandError(str(exc)) from exc
