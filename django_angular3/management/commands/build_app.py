import argparse
import datetime
import json
import subprocess
from pathlib import Path
from typing import Any
from django.core.management.base import BaseCommand, CommandError

from ...config import get_previous_schema_path, load_project_config, ConfigError
from ...tools import ensure_oasdiff


def _command_for_skill(skill: str, mode: str) -> str:
    """Maps a skill + mode pair to the corresponding management command name."""
    overrides = {
        ("ng-workspace", "create"): "ng_new",
        ("ng-workspace", "modify"): "ng_workspace_modify",
        ("ng-workspace", "delete"): "ng_workspace_delete",
        ("ng-app", "create"): "ng_gen_app",
        ("ng-app", "modify"): "ng_gen_app",
        ("ng-api", "create"): "ng_openapi_gen",
        ("ng-api", "modify"): "ng_openapi_gen",
    }
    return overrides.get((skill, mode), skill.replace("-", "_"))


class Command(BaseCommand):
    help = "Generates a deterministic build plan based on OpenAPI and config changes."

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("config", help="Path to the django-angular3.json config file.")
        parser.add_argument("--previous-schema", help="Path to previous OpenAPI schema.")
        parser.add_argument("--previous-config", help="Path to previous django-angular3.json.")
        parser.add_argument(
            "--output-format",
            choices=["json", "yaml", "text"],
            default="json",
            help="Format of the emitted build plan.",
        )
        parser.add_argument("--dry-run", action="store_true", help="Print plan without writing to disk.")
        parser.add_argument("--output", default="build", help="Directory to write the plan (build-plan.ext).")
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

    def _build_step(
        self,
        step_num: int,
        skill: str,
        mode: str,
        reason: str,
        config_path: str,
        resource_name: str | None = None,
    ) -> dict[str, object]:
        cmd_name = _command_for_skill(skill, mode)
        base_cmd = f"django-admin {cmd_name} {config_path}"
        if resource_name:
            base_cmd += f" --resource {resource_name}"
        step: dict[str, Any] = {
            "step": step_num,
            "skill": skill,
            "mode": mode,
            "reason": reason,
            "command": base_cmd,
            "dry_run_command": base_cmd + " --dry-run",
        }
        if resource_name:
            step["resource_name"] = resource_name
        return step

    def _diff_schemas(self, previous_schema: str, current_schema: str) -> dict[str, Any]:
        oasdiff_exe = ensure_oasdiff()
        
        cmd: list[str] = [
            oasdiff_exe,
            "diff",
            previous_schema,
            current_schema,
            "--format", "json"
        ]
        
        try:
            result: subprocess.CompletedProcess[str] = subprocess.run(cmd, capture_output=True, text=True, check=True)
            if not result.stdout.strip():
                return {} # No changes
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            # oasdiff might return non-zero exit code if it finds changes or breaking changes (depending on flags)
            # Usually 'diff' returns 0, but if there's an error parsing the spec, it might fail.
            try:
                if e.stdout.strip():
                    return json.loads(e.stdout)
            except json.JSONDecodeError:
                pass
            raise CommandError(f"oasdiff failed: {e.stderr}")
            
    def _extract_resources(self, path_list: list[str], path_dict: dict[str, Any]) -> set[str]:
        """Extracts base resource names from OpenAPI paths like '/api/v1/customers/' -> 'customers'."""
        resources: set[str] = set()
        
        # Handle lists (added/deleted)
        for p in path_list:
            parts: list[str] = [part for part in p.split("/") if part and not part.startswith("{")]
            if parts:
                resources.add(parts[-1]) # Rough heuristic for resource name
                
        # Handle dicts (modified)
        for p in path_dict.keys():
            parts: list[str] = [part for part in p.split("/") if part and not part.startswith("{")]
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

    def _diff_config(self, previous_config_path: str, current_config_path: str) -> dict[str, Any]:
        try:
            prev_cfg = load_project_config(previous_config_path)
            curr_cfg = load_project_config(current_config_path)
        except ConfigError as e:
            raise CommandError(f"Config load failed: {e}")
            
        if prev_cfg.project_name != curr_cfg.project_name:
            return {"type": "replace-things"} # project rename implies scratch 
            
        return {
            "type": "no-change",
            "affected_pages": [],
            "affected_components": [],
            "affected_forms": []
        }

    def handle(self, *args: list[str], **options: dict[str, Any]) -> None:
        config_path: str | Any = options["config"]

        try:
            current_config = load_project_config(config_path)
        except ConfigError as exc:
            raise CommandError(str(exc))

        current_schema_path: Path = current_config.openapi_source
        if not current_schema_path:
            raise CommandError("Config missing openapi.source")

        # Resolve previous schema: if not provided via --previous-schema, auto-discover
        # the conventional .previous artifact written by export_schema.
        prev_schema_path: str | Any = options["previous_schema"]
        if not prev_schema_path:
            auto_previous = get_previous_schema_path(current_config.openapi_source)
            if auto_previous.exists():
                prev_schema_path = str(auto_previous)
                self.stdout.write(f"Auto-detected previous schema: {prev_schema_path}")

        # Ensure we have oasdiff installed via JIT
        try:
            ensure_oasdiff()
        except RuntimeError as e:
            raise CommandError(str(e))

        change_set: dict[str, Any] = {
            "schema": {
                "type": "start-from-scratch",
                "affected_resources": [],
                "breaking": False,
                "oasdiff_report": None
            },
            "config": {
                "type": "no-change",
                "affected_pages": [],
                "affected_components": [],
                "affected_forms": []
            }
        }

        # 1. Schema Change Detection
        if str(options["force"]) == "start-from-scratch" or not prev_schema_path or not Path(prev_schema_path).exists():
            change_set["schema"]["type"] = "start-from-scratch"
            
            # To extract resources for start-from-scratch, we diff against an empty spec
            import tempfile
            with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as f:
                json.dump({"openapi": "3.0.0", "info": {"title": "empty", "version": "1.0.0"}, "paths": {}}, f)
                empty_schema_path = f.name
                
            try:
                diff_result: dict[str, Any] = self._diff_schemas(empty_schema_path, current_schema_path)
                schema_changes = self._evaluate_schema_changes(diff_result)
                # Keep type as start-from-scratch, but inherit the affected resources
                change_set["schema"]["affected_resources"] = schema_changes["affected_resources"]
                change_set["schema"]["oasdiff_report"] = diff_result
            finally:
                Path(empty_schema_path).unlink(missing_ok=True)
                
        else:
            self.stdout.write("Running oasdiff for schema changes...")
            
            # Detect structural diffs
            diff_result = self._diff_schemas(prev_schema_path, current_schema_path)
            schema_changes = self._evaluate_schema_changes(diff_result)
            
            # Detect breaking changes using `oasdiff breaking`
            cmd_break: list[str] = [ensure_oasdiff(), "breaking", prev_schema_path, str(current_schema_path), "--format", "json"]
            try:
                break_result = subprocess.run(cmd_break, capture_output=True, text=True, check=False)
                break_json: list[dict[str, Any]] = json.loads(break_result.stdout) if break_result.stdout.strip() else []
                if break_json:
                    schema_changes["breaking"] = True
            except Exception:
                pass

            if schema_changes["breaking"] and not options["acknowledge_breaking"]:
                if callable(getattr(self.style, 'ERROR', None)):
                    self.stderr.write(self.style.ERROR("Breaking schema changes detected. Review the oasdiff report before proceeding.\nRe-run with --acknowledge-breaking to continue."))
                else:
                    self.stderr.write("Breaking schema changes detected. Review the oasdiff report before proceeding.\nRe-run with --acknowledge-breaking to continue.")
                raise SystemExit(2)

            change_set["schema"] = schema_changes

        # 2. Config Change Detection
        prev_config_path: str | Any = options["previous_config"]
        if prev_config_path and Path(prev_config_path).exists():
            change_set["config"] = self._diff_config(prev_config_path, config_path)

        # 3. Build ordered steps
        schema_type = change_set["schema"]["type"]
        resources = change_set["schema"]["affected_resources"]
        steps: list[dict[str, object]] = []

        if schema_type == "start-from-scratch":
            steps.append(self._build_step(
                len(steps) + 1, "ng-workspace", "create",
                "Start from scratch: create Angular workspace",
                config_path,
            ))
            steps.append(self._build_step(
                len(steps) + 1, "ng-app", "create",
                "Start from scratch: generate Angular application",
                config_path,
            ))
            steps.append(self._build_step(
                len(steps) + 1, "ng-api", "create",
                "Start from scratch: generate API client from OpenAPI schema",
                config_path,
            ))
            for resource in resources:
                steps.append(self._build_step(
                    len(steps) + 1, "ng-data-service", "create",
                    f"Start from scratch: generate data service for '{resource}'",
                    config_path,
                    resource_name=resource,
                ))

        elif schema_type == "add-things":
            steps.append(self._build_step(
                len(steps) + 1, "ng-api", "modify",
                "Schema changed (add-things): regenerate API client",
                config_path,
            ))
            for resource in resources:
                steps.append(self._build_step(
                    len(steps) + 1, "ng-data-service", "modify",
                    f"Schema changed (add-things): update data service for '{resource}'",
                    config_path,
                    resource_name=resource,
                ))

        elif schema_type == "replace-things":
            removed = change_set["schema"].get("removed_resources", [])
            added = change_set["schema"].get("added_resources", [])
            # Delete removed resources first, then regenerate the API, then add new ones
            for resource in removed:
                steps.append(self._build_step(
                    len(steps) + 1, "ng-data-service", "delete",
                    f"Resource '{resource}' removed: delete data service",
                    config_path,
                    resource_name=resource,
                ))
            steps.append(self._build_step(
                len(steps) + 1, "ng-api", "modify",
                "Schema changed (replace-things): regenerate API client",
                config_path,
            ))
            for resource in added:
                steps.append(self._build_step(
                    len(steps) + 1, "ng-data-service", "modify",
                    f"Resource '{resource}' added: create or update data service",
                    config_path,
                    resource_name=resource,
                ))

        elif schema_type == "remove-things":
            steps.append(self._build_step(
                len(steps) + 1, "ng-api", "modify",
                "Schema changed (remove-things): regenerate API client",
                config_path,
            ))
            for resource in resources:
                steps.append(self._build_step(
                    len(steps) + 1, "ng-data-service", "delete",
                    f"Resource '{resource}' removed: delete data service",
                    config_path,
                    resource_name=resource,
                ))

        build_plan: dict[str, Any] = {
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "config": config_path,
            "change_set": change_set,
            "steps": steps,
        }

        self._emit_plan(build_plan, options)

    def _emit_plan(self, build_plan: dict[str, Any], options: dict[str, Any]) -> None:
        plan_str: str = json.dumps(build_plan, indent=2)
        
        if options["dry_run"]:
            self.stdout.write("--- DRY RUN: Build Plan ---")
            self.stdout.write(plan_str)
            return
            
        out_dir = Path(options["output"])
        out_dir.mkdir(parents=True, exist_ok=True)
        ext = options["output_format"]
        
        out_file = out_dir / f"build-plan.{ext}"
        out_file.write_text(plan_str, encoding="utf-8")
        if not callable(getattr(self.style, 'SUCCESS', None)):
            self.stdout.write(f"Build plan written to {out_file}")
        else:
            self.stdout.write(self.style.SUCCESS(f"Build plan written to {out_file}"))
