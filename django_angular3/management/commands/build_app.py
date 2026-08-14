"""
Django Angular3 Management Command: Build App

This module implements the build_app management command for building the 
Django Angular3 application.
"""
import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from django_angular3.config import ProjectConfig

from ...config import ConfigError, load_project_config
from ...tools import ensure_oasdiff

class OpenAPIConfiguration:
    '''
    Docstring for OpenAPIConfiguration
    
    :var input: Description
    :vartype input: paths
    :var output: Description
    :vartype output: loaded
    '''
    def __init__(self, openapi_path: Path):
        self._openapi_path = openapi_path

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
    '''
    Docstring for OpenUIConfiguration
    
    :var input: Description
    :vartype input: paths
    :var output: Description
    :vartype output: loaded
    '''
    def __init__(self, openui_path: Path):
        self.openui_path: Path = openui_path
        self.openui_spec: dict[str, Any] | None = None

    def load(self):
        """
        Load the OpenUI specification from the specified path.
        Raises ConfigError if loading fails.
        """
        try:
            raise NotImplementedError("Loading OpenUI specification is not implemented.")
        except ConfigError as e:
            raise CommandError(f"Failed to load OpenUI specification: {e}") from e

class Configuration:
    '''
    Docstring for Configuration


    Configuration class responsible for:
    * Loading project configuration from specified paths or default locations.
    * Managing OpenAPI configuration using the OpenAPIConfiguration class
    * Managing OpenUI configuration using the OpenUIConfiguration class
    * Managing project configuration using the ProjectConfiguration class

    var input: paths to project configuration file.
    var output: loaded configuration objects for each type.
    '''
    def __init__(self, project_config_path: str | None = None):
        self._project_config_path: str | None = project_config_path
        self._openapi_config: OpenAPIConfiguration | None = None
        self._openui_config: OpenUIConfiguration | None = None
        self._load()

    def _load(self):
        '''
        Docstring for load
        
        :param self: Description
        '''
        # Load Project configuration
        self._project_config: ProjectConfig = load_project_config(self._project_config_path)
        # Load OpenAPI configuration
        self._openapi_config = OpenAPIConfiguration(self._project_config.openapi_schema)
        # Load OpenUI configuration
        self._openui_config = OpenUIConfiguration(self._project_config.openui_specification)

class ChangeDetector:
    '''
    Docstring for ChangeDetector

    ChangeDetector class responsible for:
    * Comparing current and previous configurations to detect changes.
    * Determining the type of change (add, remove, modify, no-change).
    * Identifying affected resources based on the detected changes.
    '''
    def __init__(self, current_config: OpenAPIConfiguration, previous_config: OpenAPIConfiguration):
        self._current_config: OpenAPIConfiguration = current_config
        self._previous_config: OpenAPIConfiguration = previous_config

    def _diff_openapi_schemas(self) -> dict[str, Any]:
        oasdiff_exe = ensure_oasdiff()

        cmd: list[Path | str] = [
            oasdiff_exe,
            "diff",
            self._previous_config.openapi_schema,
            self._current_config.openapi_schema,
            "--format",
            "json",
        ]

        try:
            result: subprocess.CompletedProcess[str] = subprocess.run(
                cmd, capture_output=True, text=True, check=True
            )
            if not result.stdout.strip():
                return {}  # No changes
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            # oasdiff might return non-zero exit code if it finds changes
            # or breaking changes, depending on flags. Usually 'diff'
            # returns 0, but if there's an error parsing the spec, it
            # might fail.
            try:
                if e.stdout.strip():
                    return json.loads(e.stdout)
            except json.JSONDecodeError:
                pass
            raise CommandError(f"oasdiff failed: {e.stderr}") from e


    def detect_changes(self) -> dict[str, Any]:
        """
        Detect changes between the current and previous configurations.

        :return: A dictionary summarizing the detected changes.
        """
        try:
            raise NotImplementedError("Change detection is not implemented.")
        except ConfigError as e:
            raise CommandError(f"Failed to detect changes: {e}") from e

class ChangeExecution:
    '''
    Docstring for ChangeExecution

    ChangeExecution class responsible for:
    * Executing changes based on the detected differences.
    * Managing the order of execution and handling dependencies.
    * Rolling back changes in case of failures.
    '''
    def __init__(self, change_set: dict[str, Any]):
        self._change_set = change_set

    def execute(self):
        """
        Execute the changes based on the detected differences.

        Raises CommandError if execution fails.
        """
        try:
            raise NotImplementedError("Change execution is not implemented.")
        except ConfigError as e:
            raise CommandError(f"Failed to execute changes: {e}") from e

class Command(BaseCommand):
    '''
    Command class responsible for:
    * Parsing command-line arguments.
    * Coordinating the build process.
    * Handling change detection and execution.
    '''
    help = "Build the application frontend as described by the configuration files."

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--current-config",
            type=str,
            help="Path to current configuration: \n" \
                "The user is responsible for providing it.\n" \
                "The default is calculated from Django as follows:\n" \
                "- located at the root folder\n" \
                "- project_name calculated from Django\n" \
                "- file name is django-angular3-<project_name>.json"
        )
        parser.add_argument(
            "--previous-config",
            type=str,
            help="Path to previous configuration: \n" \
                "If not provided, path name will be the same as the current\n" \
                "with .json replaced by .previous.json.\n" \
                "if none existing, it will be treated as a start-from-scratch build."
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print the build stages without running them",
        )
        parser.add_argument(
            "--output",
            default="build",
            help="Directory to write the stagesplan (build-plan.ext).",
        )
        parser.add_argument(
            "--force",
            choices=["start-from-scratch"],
            help="Override change detection; treat as start-from-scratch.",
        )
        parser.add_argument(
            "--acknowledge-breaking",
            action="store_true",
            help="Proceed even if breaking schema changes are detected.",
        )

    def _extract_resources(
        self, path_list: list[str], path_dict: dict[str, Any]
    ) -> set[str]:
        """Extract base resource names from OpenAPI paths like
        '/api/v1/customers/' -> 'customers'."""
        resources: set[str] = set()

        # Handle lists (added/deleted)
        for p in path_list:
            parts: list[str] = [
                part for part in p.split("/") if part and not part.startswith("{")
            ]
            if parts:
                resources.add(parts[-1])  # Rough heuristic for resource name

        # Handle dicts (modified)
        for p in path_dict.keys():
            parts: list[str] = [
                part for part in p.split("/") if part and not part.startswith("{")
            ]
            if parts:
                resources.add(parts[-1])

        return resources

    def _evaluate_schema_changes(self, diff_result: dict[str, Any]) -> dict[str, Any]:
        paths_diff = diff_result.get("paths", {})
        added_paths = paths_diff.get("added", [])
        deleted_paths = paths_diff.get("deleted", [])
        modified_paths = paths_diff.get("modified", {})

        added = len(added_paths) > 0
        deleted = len(deleted_paths) > 0
        modified = len(modified_paths) > 0

        added_resources = self._extract_resources(added_paths, {})
        removed_resources = self._extract_resources(deleted_paths, {})
        modified_resources = self._extract_resources([], modified_paths)
        affected_resources = added_resources | removed_resources | modified_resources

        if added and not deleted and not modified:
            change_type = "add-things"
        elif deleted and not added and not modified:
            change_type = "remove-things"
        elif added or deleted or modified:
            change_type = "replace-things"
        else:
            change_type = "no-change"

        return {
            "type": change_type,
            "affected_resources": sorted(affected_resources),
            "added_resources": sorted(added_resources),
            "removed_resources": sorted(removed_resources),
            "breaking": False,
            "oasdiff_report": diff_result,
        }

    def _diff_config(
        self, prev_cfg: ProjectConfig, curr_cfg: ProjectConfig
    ) -> dict[str, Any]:

        if prev_cfg.project_name != curr_cfg.project_name:
            return {"type": "replace-things"}  # project rename implies scratch

        return {
            "type": "no-change",
            "affected_pages": [],
            "affected_components": [],
            "affected_forms": [],
        }

    def _diff_openui_spec(
        self, previous_openui_spec_path: str, current_openui_spec_path: str
    ):
        """
        Compare two OpenUI spec JSON files and return a summary of changes.
        Use openui-spec compare_openui_json.py command to calculate differences.

        :param previous_openui_spec_path: Previous OpenUI spec json file path
        :type previous_openui_spec_path: str
        :param current_openui_spec_path: Current OpenUI spec json file path
        :type current_openui_spec_path: str

        :raises CommandError: If loading the OpenUI spec fails
        :return: A summary of changes and commands to execute
        """
        try:
            raise NotImplementedError("OpenUI spec diffing is not implemented yet.")
        except ConfigError as e:
            raise CommandError(f"Config load failed: {e}") from e

    def _print_debug_change_set(
        self, build_plan: dict[str, Any], options: dict[str, Any]
    ) -> None:
        plan_str: str = json.dumps(build_plan, indent=2)

        out_dir = Path(options["output"])
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / "build-stages.json"
        out_file.write_text(plan_str, encoding="utf-8")
        self.stdout.write(f"Build stages were written to {out_file}")

    def handle(self, *args: Any, **options: Any) -> None:
        """build the missing pieces for a complete Angular implementation
        of the requested changes.

        The build process is a multi-step operation that involves:
        1. Load current and previous configurations.
        2. Compare current with previous configurations and derive a change set.
        3. Translate the change set into a directed graph of steps.
        4. Execute the steps in order, respecting dependencies.

        Configuration management is delegated to a Configuration class - covering steps 1 and 2.
        Change detection and derivation is delegated to ChangeDetector class - covering step 3.
        Change execution is delegated to ChangeExecution class - covering step 4.

        Raises:
            CommandError: If the configuration is invalid, its schema source is
                absent, or ``oasdiff`` cannot be prepared or used.
            SystemExit: With status 2 when breaking schema changes are found
                without ``--acknowledge-breaking``.
        """
        try:            
            current_project_config = Configuration(options["current-config"])
            previous_project_config = Configuration(options["previous-config"])
            change_detector = ChangeDetector(current_project_config,
                                             previous_project_config)
            
        except ConfigError as exc:
            raise CommandError(str(exc)) from exc

        raise NotImplementedError("build_app planning is not implemented.")
