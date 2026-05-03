import argparse
import json
import subprocess
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from ...config import load_project_config, ConfigError
from ...tools import ensure_oasdiff


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

    def _diff_schemas(self, previous_schema: str, current_schema: str) -> dict:
        oasdiff_exe = ensure_oasdiff()
        
        cmd = [
            oasdiff_exe,
            "diff",
            previous_schema,
            current_schema,
            "--format", "json"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
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
            
    def _extract_resources(self, path_list: list, path_dict: dict) -> set:
        """Extracts base resource names from OpenAPI paths like '/api/v1/customers/' -> 'customers'."""
        resources = set()
        
        # Handle lists (added/deleted)
        for p in path_list:
            parts = [part for part in p.split("/") if part and not part.startswith("{")]
            if parts:
                resources.add(parts[-1]) # Rough heuristic for resource name
                
        # Handle dicts (modified)
        for p in path_dict.keys():
            parts = [part for part in p.split("/") if part and not part.startswith("{")]
            if parts:
                resources.add(parts[-1])
                
        return resources

    def _evaluate_schema_changes(self, diff_result: dict) -> dict:
        paths_diff = diff_result.get("paths", {})
        added_paths = paths_diff.get("added", [])
        deleted_paths = paths_diff.get("deleted", [])
        modified_paths = paths_diff.get("modified", {})
        
        added = len(added_paths) > 0
        deleted = len(deleted_paths) > 0
        modified = len(modified_paths) > 0
        
        affected_resources = set()
        affected_resources.update(self._extract_resources(added_paths, {}))
        affected_resources.update(self._extract_resources(deleted_paths, {}))
        affected_resources.update(self._extract_resources([], modified_paths))
        
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
            "affected_resources": sorted(list(affected_resources)),
            "breaking": False,
            "oasdiff_report": diff_result
        }

    def _diff_config(self, previous_config_path: str, current_config_path: str) -> dict:
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

    def handle(self, *args, **options) -> None:
        config_path = options["config"]
        prev_schema_path = options["previous_schema"]
        
        try:
            current_config = load_project_config(config_path)
        except ConfigError as exc:
            raise CommandError(str(exc))
            
        current_schema_path = current_config.openapi_source
        if not current_schema_path:
            raise CommandError("Config missing openapi.source")
            
        # Ensure we have oasdiff installed via JIT
        self.stdout.write("Checking dependencies...")
        try:
            ensure_oasdiff()
        except RuntimeError as e:
            raise CommandError(str(e))

        change_set = {
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
        if options["force"] == "start-from-scratch" or not prev_schema_path or not Path(prev_schema_path).exists():
            change_set["schema"]["type"] = "start-from-scratch"
            
            # To extract resources for start-from-scratch, we diff against an empty spec
            import tempfile
            with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as f:
                json.dump({"openapi": "3.0.0", "info": {"title": "empty", "version": "1.0.0"}, "paths": {}}, f)
                empty_schema_path = f.name
                
            try:
                diff_result = self._diff_schemas(empty_schema_path, current_schema_path)
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
            
            # Detect Breaking Changes using `oasdiff breaking`
            cmd_break = [ensure_oasdiff(), "breaking", prev_schema_path, current_schema_path, "--format", "json"]
            try:
                break_result = subprocess.run(cmd_break, capture_output=True, text=True, check=False)
                break_json = json.loads(break_result.stdout) if break_result.stdout.strip() else []
                if break_json:
                    schema_changes["breaking"] = True
                    schema_changes["type"] = "breaking"
            except Exception:
                pass
                
            if schema_changes["breaking"] and not options["acknowledge_breaking"]:
                self.stderr.write(self.style.ERROR(
                    "Breaking schema changes detected. Review the oasdiff report before proceeding.\n"
                    "Re-run with --acknowledge-breaking to continue."
                ))
                return
                
            change_set["schema"] = schema_changes

        # 2. Config Change Detection
        prev_config_path = options["previous_config"]
        if prev_config_path and Path(prev_config_path).exists():
            change_set["config"] = self._diff_config(prev_config_path, config_path)

        # 3. Create the build plan
        build_plan = {
            "change_set": change_set,
            "steps": []
        }

        # Determine steps via Skill Mapping hierarchy
        schema_type = change_set["schema"]["type"]
        resources = change_set["schema"]["affected_resources"]

        if schema_type == "start-from-scratch":
            build_plan["steps"].append({"step": 1, "skill": "ng-workspace", "mode": "create"})
            build_plan["steps"].append({"step": 2, "skill": "ng-app", "mode": "create"})
            build_plan["steps"].append({"step": 3, "skill": "ng-api", "mode": "create"})
            for i, resource in enumerate(resources, start=4):
                build_plan["steps"].append({"step": i, "skill": "ng-data-service", "mode": "create", "resource_name": resource})

        elif schema_type in ("add-things", "replace-things"):
            build_plan["steps"].append({"step": 1, "skill": "ng-api", "mode": "modify"})
            for i, resource in enumerate(resources, start=2):
                build_plan["steps"].append({"step": i, "skill": "ng-data-service", "mode": "modify", "resource_name": resource})

        elif schema_type == "remove-things":
            build_plan["steps"].append({"step": 1, "skill": "ng-api", "mode": "modify"})
            for i, resource in enumerate(resources, start=2):
                build_plan["steps"].append({"step": i, "skill": "ng-data-service", "mode": "delete", "resource_name": resource})

        self._emit_plan(build_plan, options)
        
    def _emit_plan(self, build_plan: dict, options: dict) -> None:
        plan_str = json.dumps(build_plan, indent=2)
        
        if options["dry_run"]:
            self.stdout.write("--- DRY RUN: Build Plan ---")
            self.stdout.write(plan_str)
            return
            
        out_dir = Path(options["output"])
        out_dir.mkdir(parents=True, exist_ok=True)
        ext = options["output_format"]
        
        out_file = out_dir / f"build-plan.{ext}"
        out_file.write_text(plan_str, encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Build plan written to {out_file}"))
