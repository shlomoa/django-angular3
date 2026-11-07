"""Credential-free tests of the lifecycle Hooks, their registry and their artifacts."""

import io
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from django_angular3 import command_execution
from django_angular3.automation.contracts import (
    EXIT_HOOK_FAILURE,
    EXIT_OK,
    EXIT_TOOL_FAILURE,
    ContractError,
    FailureCategory,
    HookFamily,
)
from django_angular3.automation.execution import (
    DirectExecutor,
    ExecutionContext,
    HookObservation,
    ToolCall,
)
from django_angular3.automation.hooks import (
    HISTORY,
    HOOK_LOG,
    MAKEMIGRATIONS,
    SESSION_LOG,
    SESSION_STOP,
    SESSION_TIMESTAMP,
    VERIFICATION_LOG,
    HookRegistration,
    HookRegistry,
    command_identity,
    default_registry,
    observation_from_provider,
    snapshot_migrations,
)
from django_angular3.automation.migrations import (
    migrations_fingerprint,
    read_record,
    write_record,
)
from tests.test_step_execution import _Project
from tests.tool_config import use_tool_configuration_template

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = {
    "openapi": "3.1.0",
    "info": {"title": "t", "version": "1"},
    "paths": {"/api/v1/x/": {"get": {"responses": {"200": {"description": "ok"}}}}},
}


def setUpModule() -> None:
    use_tool_configuration_template()


class HookTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.project = _Project(self)
        self.root = self.project.root
        self.build = self.root / "build"
        self.stderr = io.StringIO()
        self.registry = default_registry(lambda: "20260101T000000Z", self.stderr)
        self.context = ExecutionContext(
            self.project.project_config,
            self.build,
            "run-1",
            settings=self.project.settings,
        )
        self.schema = self.project.project_config.openapi_schema
        self.schema.write_text(json.dumps(SCHEMA), encoding="utf-8")

    def executor(self, session_stop: bool = False) -> DirectExecutor:
        """The registry's Hooks; session-stop archives the logs, so it is opt-in."""
        bindings = [
            b
            for b in self.registry.bindings()
            if session_stop or b.family is not HookFamily.SESSION_STOP
        ]
        return DirectExecutor(self.context, bindings)

    def log(self, name: str = HOOK_LOG) -> list[dict]:
        path = self.build / name
        if not path.is_file():
            return []
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line
        ]

    def add_migration(self, name: str = "0001_initial.py") -> Path:
        directory = self.root / "shop" / "migrations"
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "__init__.py").write_text("", encoding="utf-8")
        path = directory / name
        path.write_text("# migration\n", encoding="utf-8")
        return path


class PreConstructionTests(HookTestCase):
    def run_scaffold(self):
        ran = []

        def scaffold(context, inputs):
            ran.append(1)
            return {"generated_files": []}

        result = self.executor().run([ToolCall("angular_app_scaffold", scaffold)])
        return result, ran

    def test_a_valid_fresh_schema_lets_the_tool_run(self) -> None:
        result, ran = self.run_scaffold()

        self.assertEqual(ran, [1])
        self.assertTrue(result.steps[0].hooks[0].ok, result.steps[0].hooks[0].failure)
        (record,) = [r for r in self.log() if r["hook"] == "pre-construction"]
        self.assertEqual(record["hook"], "pre-construction")
        self.assertIs(record["pass"], True)

    def test_a_missing_schema_blocks_and_is_logged(self) -> None:
        self.schema.unlink()

        result, ran = self.run_scaffold()

        self.assertEqual(ran, [])
        self.assertEqual(result.steps[0].status, "blocked")
        record = self.log()[0]
        self.assertEqual(record["hook"], "pre-construction")
        self.assertEqual(record["reason"], "missing")
        self.assertEqual(record["schema_path"], str(self.schema))
        self.assertEqual(json.loads(self.stderr.getvalue().splitlines()[0]), record)
        self.assertEqual(result.exit_code, EXIT_HOOK_FAILURE)

    def test_a_schema_exported_against_other_migrations_is_stale(self) -> None:
        self.add_migration()
        write_record(self.schema, self.root)
        self.add_migration("0002_more.py")

        result, ran = self.run_scaffold()

        self.assertEqual(ran, [])
        self.assertEqual(self.log()[0]["reason"], "stale")
        self.assertEqual(result.exit_code, EXIT_HOOK_FAILURE)

    def test_a_schema_with_a_matching_record_passes_whatever_the_file_times(
        self,
    ) -> None:
        migration = self.add_migration()
        write_record(self.schema, self.root)
        # A checkout or a copy orders the file times at random.
        os.utime(self.schema, ns=(1_000_000_000, 1_000_000_000))
        os.utime(migration, ns=(9_000_000_000, 9_000_000_000))

        result, ran = self.run_scaffold()

        self.assertEqual(ran, [1])
        self.assertTrue(result.steps[0].hooks[0].ok, result.steps[0].hooks[0].failure)

    def test_a_schema_without_a_record_is_never_blocked_as_stale(self) -> None:
        migration = self.add_migration()
        os.utime(self.schema, ns=(1_000_000_000, 1_000_000_000))
        os.utime(migration, ns=(9_000_000_000, 9_000_000_000))

        result, ran = self.run_scaffold()

        self.assertEqual(ran, [1])
        self.assertTrue(result.steps[0].hooks[0].ok, result.steps[0].hooks[0].failure)

    def test_a_changed_migration_content_changes_the_fingerprint(self) -> None:
        migration = self.add_migration()
        before = migrations_fingerprint(self.root)

        migration.write_text("# changed\n", encoding="utf-8")

        self.assertNotEqual(migrations_fingerprint(self.root), before)
        self.assertEqual(read_record(self.schema), None)

    def test_an_invalid_schema_blocks_and_the_hook_never_repairs_it(self) -> None:
        self.schema.write_text(json.dumps({"openapi": "3.1.0"}), encoding="utf-8")
        before = self.schema.read_bytes()

        result, ran = self.run_scaffold()

        self.assertEqual(ran, [])
        self.assertEqual(self.log()[0]["reason"], "invalid")
        self.assertEqual(self.schema.read_bytes(), before)

    def test_it_does_not_wrap_tools_outside_its_scope(self) -> None:
        self.schema.unlink()

        result = self.executor().run(
            [ToolCall("oasdiff_diff", lambda context, inputs: {})]
        )

        self.assertTrue(result.ok)
        self.assertEqual(self.log(), [])


class MigrationTriggeredTests(HookTestCase):
    def run_makemigrations(self, create: bool):
        before = snapshot_migrations(self.context)

        def makemigrations(context, inputs):
            if create:
                self.add_migration()
            return {}

        call = ToolCall(MAKEMIGRATIONS, makemigrations, {"migrations_before": before})
        return self.executor().run([call])

    def export_result(self, output=None, error=None):
        def fake(context, inputs):
            if error:
                raise ContractError(FailureCategory.EXTERNAL_TOOL_FAILED, error)
            return output

        return patch("django_angular3.automation.tools.openapi_schema_export", fake)

    def test_a_new_migration_triggers_the_export_and_is_logged(self) -> None:
        output = {
            "destination": str(self.schema),
            "previous_path": None,
            "schema_changed": True,
        }
        with self.export_result(output):
            result = self.run_makemigrations(create=True)

        self.assertTrue(result.ok, result.failure)
        record = self.log()[0]
        self.assertEqual(record["hook"], "migration-triggered")
        self.assertEqual(record["migrations"], ["shop/migrations/0001_initial.py"])
        self.assertEqual(record["destination"], str(self.schema))
        self.assertIs(record["schema_changed"], True)

    def test_no_migration_change_triggers_nothing(self) -> None:
        with self.export_result(error="must not be called"):
            result = self.run_makemigrations(create=False)

        self.assertTrue(result.ok)
        self.assertEqual(self.log(), [])

    def test_an_export_failure_halts_and_keeps_the_migration(self) -> None:
        with self.export_result(error="spectacular failed"):
            result = self.run_makemigrations(create=True)

        self.assertFalse(result.ok)
        self.assertEqual(result.exit_code, EXIT_HOOK_FAILURE)
        self.assertTrue((self.root / "shop/migrations/0001_initial.py").is_file())
        record = self.log()[0]
        self.assertEqual(record["hook"], "migration-triggered")
        self.assertIn("spectacular failed", record["message"])

    def test_it_only_wraps_the_makemigrations_command(self) -> None:
        with self.export_result(error="must not be called"):
            result = self.executor().run(
                [ToolCall("angular_app_scaffold", lambda c, i: {"generated_files": []})]
            )
        self.assertNotIn(
            "migration-triggered", [h.hook for s in result.steps for h in s.hooks]
        )


class PostGenerationTests(HookTestCase):
    def scaffold(self, create_files: bool):
        workspace = self.project.workspace
        name = self.project.project_config.project_name

        def tool(context, inputs):
            if create_files:
                (workspace / "projects" / name / "src").mkdir(
                    parents=True, exist_ok=True
                )
            return {"generated_files": ["projects/x/src/main.ts"]}

        return self.executor().run([ToolCall("angular_app_scaffold", tool)])

    def test_a_pass_is_logged_with_its_files_and_timestamp(self) -> None:
        result = self.scaffold(create_files=True)

        self.assertTrue(result.ok, result.failure)
        (entry,) = self.log(VERIFICATION_LOG)
        self.assertEqual(entry["hook"], "post-generation")
        self.assertEqual(entry["tool"], "angular_app_scaffold")
        self.assertIs(entry["pass"], True)
        self.assertEqual(entry["generated_files"], ["projects/x/src/main.ts"])
        self.assertEqual(entry["timestamp"], "20260101T000000Z")

    def test_a_failing_check_is_logged_and_halts(self) -> None:
        result = self.scaffold(create_files=False)

        self.assertFalse(result.ok)
        self.assertEqual(result.exit_code, EXIT_HOOK_FAILURE)
        (entry,) = self.log(VERIFICATION_LOG)
        self.assertIs(entry["pass"], False)
        self.assertIn("missing", entry["details"])

    def test_it_never_modifies_the_generated_artifacts(self) -> None:
        self.scaffold(create_files=True)
        before = sorted(
            p.relative_to(self.project.workspace).as_posix()
            for p in self.project.workspace.rglob("*")
            if p.is_file()
        )

        self.scaffold(create_files=True)

        after = sorted(
            p.relative_to(self.project.workspace).as_posix()
            for p in self.project.workspace.rglob("*")
            if p.is_file()
        )
        self.assertEqual(before, after)

    def test_the_client_check_runs_tsc_through_command_execution(self) -> None:
        calls = []

        def run(argv, cwd=None, check=True, **_):
            calls.append(list(argv))
            return command_execution.CommandResult(0, "", "")

        self.registry = default_registry(
            lambda: "20260101T000000Z", self.stderr, client_check="tsc"
        )
        tool = ToolCall(
            "angular_api_client_generate", lambda c, i: {"generated_files": []}
        )
        with patch(
            "django_angular3.automation.hooks.command_execution.run_command", run
        ):
            result = self.executor().run([tool])

        self.assertTrue(result.ok, result.failure)
        self.assertEqual(calls[0][1:], ["exec", "tsc", "--noEmit"])

    def test_a_failing_tsc_halts(self) -> None:
        def run(argv, cwd=None, check=True, **_):
            return command_execution.CommandResult(2, "error TS2304", "")

        self.registry = default_registry(
            lambda: "20260101T000000Z", self.stderr, client_check="tsc"
        )
        tool = ToolCall(
            "angular_api_client_generate", lambda c, i: {"generated_files": []}
        )
        with patch(
            "django_angular3.automation.hooks.command_execution.run_command", run
        ):
            result = self.executor().run([tool])

        self.assertFalse(result.ok)
        self.assertIn("TS2304", self.log(VERIFICATION_LOG)[0]["details"])


class ClientStructureTests(HookTestCase):
    def generate(self, create: bool):
        workspace = self.project.workspace
        output = "projects/shop/src/app/api"

        def tool(context, inputs):
            (workspace / "ng-openapi-gen.json").write_text(
                json.dumps({"output": output}), encoding="utf-8"
            )
            if create:
                services = workspace / output / "services"
                services.mkdir(parents=True, exist_ok=True)
                (services / "customers.service.ts").write_text("x", encoding="utf-8")
            return {}

        def no_tsc(argv, cwd=None, check=True, **_):
            raise AssertionError("tsc must not run in the middle of a build")

        with patch(
            "django_angular3.automation.hooks.command_execution.run_command", no_tsc
        ):
            return self.executor().run([ToolCall("angular_api_client_generate", tool)])

    def test_the_default_check_after_the_client_is_structural_not_tsc(self) -> None:
        result = self.generate(create=True)

        self.assertTrue(result.ok, result.failure)
        (entry,) = self.log(VERIFICATION_LOG)
        self.assertIs(entry["pass"], True)
        self.assertIn("1 generated client service", entry["details"])

    def test_a_client_without_services_halts(self) -> None:
        result = self.generate(create=False)

        self.assertFalse(result.ok)
        self.assertEqual(result.exit_code, EXIT_HOOK_FAILURE)
        self.assertIn(
            "no generated client service", self.log(VERIFICATION_LOG)[0]["details"]
        )


class SessionStopTests(HookTestCase):
    def prepare(self) -> None:
        self.build.mkdir(parents=True, exist_ok=True)
        for name in (
            HOOK_LOG,
            VERIFICATION_LOG,
            "oasdiff-report.json",
            "command-execution.1",
        ):
            (self.build / name).write_text(name, encoding="utf-8")

    def stop(self):
        return self.executor(session_stop=True).run(
            [ToolCall("oasdiff_diff", lambda c, i: {})]
        )

    def test_artifacts_are_archived_and_the_summary_recorded(self) -> None:
        self.prepare()

        self.stop()

        archived = sorted(
            p.name for p in (self.build / HISTORY / "20260101T000000Z").iterdir()
        )
        self.assertEqual(
            archived,
            sorted(
                [
                    HOOK_LOG,
                    "command-execution.1",
                    "oasdiff-report.json",
                    VERIFICATION_LOG,
                ]
            ),
        )
        self.assertFalse((self.build / VERIFICATION_LOG).exists())
        (entry,) = json.loads((self.build / SESSION_LOG).read_text(encoding="utf-8"))
        self.assertEqual(entry["hook"], SESSION_STOP)
        self.assertEqual(entry["timestamp"], "20260101T000000Z")
        self.assertEqual(entry["commands_completed"], 1)
        self.assertEqual(entry["commands_failed"], 0)
        self.assertEqual(entry["exit_code"], EXIT_OK)
        self.assertIn("schema_version", entry)

    def test_missing_artifacts_are_skipped(self) -> None:
        result = self.stop()

        self.assertTrue(result.ok)
        self.assertEqual(result.warnings, ())
        self.assertFalse((self.build / HISTORY).exists())

    def test_the_timestamp_is_persisted_and_reused(self) -> None:
        self.prepare()
        (self.build / SESSION_TIMESTAMP).write_text(
            "20250505T050505Z\n", encoding="utf-8"
        )

        self.stop()

        self.assertTrue((self.build / HISTORY / "20250505T050505Z").is_dir())

    def test_a_rerun_does_not_duplicate_archives_or_summary_entries(self) -> None:
        self.prepare()

        self.stop()
        self.stop()

        entries = json.loads((self.build / SESSION_LOG).read_text(encoding="utf-8"))
        self.assertEqual(len(entries), 1)
        self.assertEqual(len(list((self.build / HISTORY).iterdir())), 1)

    def test_an_archiving_failure_only_warns(self) -> None:
        self.prepare()

        with patch(
            "django_angular3.automation.hooks.shutil.move",
            side_effect=OSError("disk full"),
        ):
            result = self.stop()

        self.assertTrue(result.ok)
        self.assertEqual(result.exit_code, EXIT_OK)
        self.assertEqual(len(result.warnings), 1)
        self.assertIn("disk full", result.warnings[0].message)
        stderr = json.loads(self.stderr.getvalue().splitlines()[-1])
        self.assertEqual(stderr["hook"], SESSION_STOP)

    def test_the_summary_counts_failures(self) -> None:
        self.prepare()
        failing = ToolCall(
            "oasdiff_diff", lambda c, i: (_ for _ in ()).throw(RuntimeError("x"))
        )

        result = self.executor(session_stop=True).run([failing])

        self.assertEqual(result.exit_code, EXIT_TOOL_FAILURE)
        (entry,) = json.loads((self.build / SESSION_LOG).read_text(encoding="utf-8"))
        self.assertEqual(entry["commands_failed"], 1)
        self.assertEqual(entry["exit_code"], EXIT_TOOL_FAILURE)


class ExitCodeTests(unittest.TestCase):
    def test_the_hook_failure_code_is_distinct(self) -> None:
        self.assertEqual(len({EXIT_OK, EXIT_TOOL_FAILURE, EXIT_HOOK_FAILURE}), 3)


class RegistryTests(HookTestCase):
    def test_the_catalogued_hooks_are_registered_by_name_and_family(self) -> None:
        self.assertEqual(
            [(r.name, r.family.value) for r in self.registry.registrations()],
            [
                ("pre-construction", "pre-tool"),
                ("migration-triggered", "post-tool"),
                ("post-generation", "post-tool"),
                ("session-stop", "session-stop"),
            ],
        )

    def test_selection_uses_canonical_identity_only(self) -> None:
        names = lambda family, tool: [  # noqa: E731
            r.name for r in self.registry.select(family, tool)
        ]

        self.assertEqual(
            names(HookFamily.PRE_TOOL, "angular_app_scaffold"), ["pre-construction"]
        )
        self.assertEqual(names(HookFamily.PRE_TOOL, "oasdiff_diff"), [])
        self.assertEqual(
            names(HookFamily.POST_TOOL, "makemigrations"), ["migration-triggered"]
        )
        self.assertEqual(
            names(HookFamily.POST_TOOL, "bash: python manage.py makemigrations"), []
        )
        self.assertEqual(names(HookFamily.SESSION_STOP, None), ["session-stop"])

    def test_a_duplicate_registration_is_refused(self) -> None:
        registration = self.registry.registrations()[0]
        with self.assertRaises(ContractError):
            self.registry.register(registration)

    def test_a_duplicate_observation_is_idempotent(self) -> None:
        runs = []
        registry = HookRegistry()
        registry.register(
            HookRegistration(
                "counter",
                HookFamily.POST_TOOL,
                lambda context, observation: runs.append(1),
                frozenset({"t"}),
            )
        )
        observation = HookObservation(HookFamily.POST_TOOL, "t", {})

        first = registry.dispatch(self.context, observation, "call-1")
        second = registry.dispatch(self.context, observation, "call-1")
        third = registry.dispatch(self.context, observation, "call-2")

        self.assertEqual(runs, [1, 1])
        self.assertEqual(first, second)
        self.assertEqual(len(third), 1)

    def test_a_dispatched_failure_is_a_normalized_outcome(self) -> None:
        registry = HookRegistry()
        registry.register(
            HookRegistration(
                "bad",
                HookFamily.PRE_TOOL,
                lambda c, o: (_ for _ in ()).throw(KeyError("k")),
                None,
            )
        )

        (outcome,) = registry.dispatch(
            self.context, HookObservation(HookFamily.PRE_TOOL, "anything", {})
        )

        self.assertFalse(outcome.ok)
        self.assertEqual(outcome.failure.category, FailureCategory.HOOK_FAILED)


class ProviderObservationTests(unittest.TestCase):
    # Recorded shapes of the lifecycle payloads of the providers (no SDK involved).
    CLAUDE = {
        "PreToolUse": {
            "hook_event_name": "PreToolUse",
            "tool_name": "angular_app_scaffold",
            "tool_input": {"document": "a.json"},
            "tool_use_id": "toolu_1",
        },
        "PostToolUse": {
            "hook_event_name": "PostToolUse",
            "tool_name": "mcp__djng__angular_app_scaffold",
            "tool_input": {},
            "tool_use_id": "toolu_2",
        },
        "Stop": {"hook_event_name": "Stop", "session_id": "s1"},
    }
    COPILOT = {
        "on_pre_tool_use": {"toolName": "angular_app_scaffold", "toolArgs": {}},
        "on_post_tool_use": {"toolName": "angular_app_scaffold", "toolArgs": {}},
    }

    def test_claude_and_copilot_events_normalize_to_the_same_identity(self) -> None:
        claude_pre, _ = observation_from_provider(
            "claude", "PreToolUse", self.CLAUDE["PreToolUse"]
        )
        claude_post, call = observation_from_provider(
            "claude", "PostToolUse", self.CLAUDE["PostToolUse"]
        )
        stop, _ = observation_from_provider("claude", "Stop", self.CLAUDE["Stop"])
        copilot_pre, _ = observation_from_provider(
            "copilot", "on_pre_tool_use", self.COPILOT["on_pre_tool_use"]
        )
        copilot_post, _ = observation_from_provider(
            "copilot", "on_post_tool_use", self.COPILOT["on_post_tool_use"]
        )

        self.assertEqual(
            (claude_pre.family, claude_pre.tool),
            (HookFamily.PRE_TOOL, "angular_app_scaffold"),
        )
        self.assertEqual(
            (copilot_pre.family, copilot_pre.tool), (claude_pre.family, claude_pre.tool)
        )
        self.assertEqual(
            (claude_post.family, claude_post.tool),
            (HookFamily.POST_TOOL, "angular_app_scaffold"),
        )
        self.assertEqual(
            (copilot_post.family, copilot_post.tool),
            (claude_post.family, claude_post.tool),
        )
        self.assertEqual((stop.family, stop.tool), (HookFamily.SESSION_STOP, None))
        self.assertEqual(call, "toolu_2")

    def test_a_shell_command_is_identified_by_its_tokens_not_a_substring(self) -> None:
        def tool(command: str) -> str | None:
            observation, _ = observation_from_provider(
                "claude",
                "PostToolUse",
                {"tool_name": "Bash", "tool_input": {"command": command}},
            )
            return observation.tool

        self.assertEqual(tool("python manage.py makemigrations shop"), MAKEMIGRATIONS)
        self.assertEqual(tool("django-admin makemigrations --dry-run"), MAKEMIGRATIONS)
        self.assertEqual(tool("echo makemigrations"), "Bash")
        self.assertEqual(tool("python manage.py migrate"), "Bash")
        self.assertEqual(tool("cat docs/makemigrations.md"), "Bash")
        self.assertIsNone(command_identity(["ls", "makemigrations"]))

    def test_unknown_events_and_missing_tools_are_invalid_input(self) -> None:
        for provider, event, payload in (
            ("claude", "Nope", {}),
            ("other", "PreToolUse", {}),
            ("claude", "PreToolUse", {}),
        ):
            with (
                self.subTest(provider=provider, event=event),
                self.assertRaises(ContractError),
            ):
                observation_from_provider(provider, event, payload)

    def test_the_hooks_module_imports_no_provider_sdk(self) -> None:
        code = (
            "import sys, django_angular3.automation.hooks\n"
            "bad=[m for m in ('claude_agent_sdk','openai','google.genai','copilot')"
            " if m in sys.modules]\n"
            "sys.exit(1 if bad else 0)"
        )
        completed = subprocess.run(
            [sys.executable, "-I", "-c", code], cwd=ROOT, check=False
        )
        self.assertEqual(completed.returncode, 0)


if __name__ == "__main__":
    unittest.main()
