"""Credential-free tests of the direct-execution primitives."""

import json
import os
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from django_angular3 import command_execution
from django_angular3.automation.contracts import (
    ContractError,
    FailureCategory,
    HookFamily,
)
from django_angular3.automation.evidence import (
    EVIDENCE_FILE_NAME,
    JsonLinesEvidenceRecorder,
    read_events,
)
from django_angular3.automation.execution import (
    DirectExecutor,
    ExecutionContext,
    HookBinding,
    ToolCall,
    command_tool,
)
from tests.automation_samples import execution_scenarios, fixed_clock
from tests.generate_automation_goldens import GOLDEN_DIR
from tests.workspace_temp import WORKSPACE_TEMP_DIR

ROOT = Path(__file__).resolve().parent.parent


class ExecutionTestCase(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(dir=WORKSPACE_TEMP_DIR)
        self.addCleanup(temporary.cleanup)
        self.output = Path(temporary.name) / "build"

    def context(self, **overrides) -> ExecutionContext:
        recorder = JsonLinesEvidenceRecorder(self.output, "run-1", fixed_clock())
        values = {
            "project_config": None,
            "output_dir": self.output,
            "run_id": "run-1",
            "recorder": recorder,
        }
        values.update(overrides)
        return ExecutionContext(**values)

    def events(self) -> list[dict]:
        return list(read_events(self.output / EVIDENCE_FILE_NAME).events)

    def names(self) -> list[str]:
        return [
            f"{e['kind']}:{e.get('name', '')}"
            for e in self.events()
            if e["kind"] != "run"
        ]


def _ok(context, inputs):
    return {"done": True}


def _raise(error):
    def run(context, inputs):
        raise error

    return run


def _hook(error=None):
    def run(context, observation):
        if error is not None:
            raise error

    return run


class ConsequenceTests(ExecutionTestCase):
    def test_a_pre_tool_failure_blocks_its_tool_which_never_runs(self) -> None:
        ran = []

        def tool(context, inputs):
            ran.append(1)
            return {}

        hooks = [HookBinding("gate", HookFamily.PRE_TOOL, _hook(ValueError("no")))]
        result = DirectExecutor(self.context(), hooks).run([ToolCall("t", tool)])

        self.assertEqual(ran, [])
        self.assertFalse(result.ok)
        self.assertEqual(result.steps[0].status, "blocked")
        self.assertEqual(result.failure.category, FailureCategory.HOOK_FAILED)
        self.assertEqual(self.names(), ["hook:gate", "acceptance:"])

    def test_a_post_tool_failure_halts_and_suppresses_dependents(self) -> None:
        hooks = [HookBinding("check", HookFamily.POST_TOOL, _hook(ValueError("bad")))]
        second_ran = []

        def second(context, inputs):
            second_ran.append(1)
            return {}

        result = DirectExecutor(self.context(), hooks).run(
            [ToolCall("first", _ok), ToolCall("second", second)]
        )

        self.assertEqual(second_ran, [])
        self.assertEqual([s.status for s in result.steps], ["failed", "skipped"])
        self.assertFalse(result.ok)
        self.assertEqual(self.names(), ["tool:first", "hook:check", "acceptance:"])

    def test_a_session_stop_failure_only_warns(self) -> None:
        hooks = [HookBinding("archive", HookFamily.SESSION_STOP, _hook(OSError("x")))]

        result = DirectExecutor(self.context(), hooks).run([ToolCall("t", _ok)])

        self.assertTrue(result.ok)
        self.assertIsNone(result.failure)
        self.assertEqual(len(result.warnings), 1)
        self.assertEqual(result.warnings[0].category, FailureCategory.HOOK_FAILED)
        acceptance = self.events()[-1]
        self.assertEqual(acceptance["decision"], "accepted")
        self.assertEqual(acceptance["warnings"], 1)

    def test_a_session_stop_failure_does_not_change_a_failed_result(self) -> None:
        hooks = [HookBinding("archive", HookFamily.SESSION_STOP, _hook(OSError("x")))]

        result = DirectExecutor(self.context(), hooks).run(
            [ToolCall("t", _raise(RuntimeError("boom")))]
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.failure.category, FailureCategory.UNEXPECTED)
        self.assertEqual(len(result.warnings), 1)

    def test_hooks_only_wrap_the_tools_in_their_scope(self) -> None:
        hooks = [
            HookBinding(
                "other",
                HookFamily.PRE_TOOL,
                _hook(ValueError("no")),
                tools=frozenset({"unrelated"}),
            )
        ]

        result = DirectExecutor(self.context(), hooks).run([ToolCall("t", _ok)])

        self.assertTrue(result.ok)


class NormalizationTests(ExecutionTestCase):
    def test_unexpected_exceptions_are_normalized_and_recorded(self) -> None:
        for name, error, category in (
            ("unexpected", RuntimeError("boom"), FailureCategory.UNEXPECTED),
            (
                "command",
                command_execution.CommandExecutionError("exit 2"),
                FailureCategory.EXTERNAL_TOOL_FAILED,
            ),
            (
                "contract",
                ContractError(FailureCategory.OUTPUT_INVALID, "bad"),
                FailureCategory.OUTPUT_INVALID,
            ),
        ):
            with self.subTest(name):
                self.output = self.output.parent / name
                result = DirectExecutor(self.context(), []).run(
                    [ToolCall("t", _raise(error))]
                )

                self.assertFalse(result.ok)
                self.assertEqual(result.failure.category, category)
                tool_event = next(e for e in self.events() if e["kind"] == "tool")
                self.assertEqual(tool_event["failure"]["category"], category.value)

    def test_a_hook_exception_is_normalized(self) -> None:
        hooks = [HookBinding("h", HookFamily.POST_TOOL, _hook(KeyError("k")))]

        result = DirectExecutor(self.context(), hooks).run([ToolCall("t", _ok)])

        self.assertEqual(result.failure.category, FailureCategory.HOOK_FAILED)

    def test_a_recorder_failure_halts_with_a_structured_failure(self) -> None:
        context = self.context()
        with patch("pathlib.Path.open", side_effect=OSError("disk full")):
            result = DirectExecutor(context, []).run([ToolCall("t", _ok)])

        self.assertFalse(result.ok)
        self.assertEqual(result.failure.category, FailureCategory.EVIDENCE_WRITE_FAILED)
        self.assertEqual([s.status for s in result.steps], ["skipped"])


class EvidenceOrderTests(ExecutionTestCase):
    def test_events_follow_execution_order(self) -> None:
        hooks = [
            HookBinding("pre", HookFamily.PRE_TOOL, _hook()),
            HookBinding("post", HookFamily.POST_TOOL, _hook()),
            HookBinding("stop", HookFamily.SESSION_STOP, _hook()),
        ]

        DirectExecutor(self.context(), hooks).run(
            [ToolCall("a", _ok), ToolCall("b", _ok)]
        )

        self.assertEqual(
            self.names(),
            [
                "hook:pre",
                "tool:a",
                "hook:post",
                "hook:pre",
                "tool:b",
                "hook:post",
                "hook:stop",
                "acceptance:",
            ],
        )
        self.assertEqual(
            [e["seq"] for e in self.events()], list(range(1, 1 + len(self.events())))
        )

    def test_each_consequence_matches_its_generated_golden_transcript(self) -> None:
        for name, (calls, hooks) in execution_scenarios().items():
            with self.subTest(name):
                self.output = self.output.parent / name
                DirectExecutor(self.context(), hooks).run(calls)

                golden = (GOLDEN_DIR / f"{name}.jsonl").read_bytes()
                self.assertEqual(
                    (self.output / EVIDENCE_FILE_NAME).read_bytes(), golden
                )


class ProcessPathTests(ExecutionTestCase):
    def test_a_command_tool_starts_processes_only_through_command_execution(
        self,
    ) -> None:
        tool = command_tool(lambda inputs: ["echo", inputs["word"]])
        fake = command_execution.CommandResult(0, "hi\n", "")

        with (
            patch(
                "django_angular3.automation.execution.command_execution.run_command",
                return_value=fake,
            ) as run_command,
            patch("subprocess.run") as subprocess_run,
        ):
            result = DirectExecutor(self.context(), []).run(
                [ToolCall("echo", tool, {"word": "hi"})]
            )

        run_command.assert_called_once()
        subprocess_run.assert_not_called()
        self.assertEqual(result.steps[0].result.output["stdout"], "hi\n")

    def test_a_failing_command_is_an_external_tool_failure(self) -> None:
        tool = command_tool(
            lambda inputs: [sys.executable, "-c", "raise SystemExit(3)"]
        )

        result = DirectExecutor(self.context(), []).run([ToolCall("fails", tool)])

        self.assertEqual(result.failure.category, FailureCategory.EXTERNAL_TOOL_FAILED)


class ExistingBehaviorTests(unittest.TestCase):
    def test_existing_django_command_errors_are_preserved(self) -> None:
        from django.core.management import call_command
        from django.core.management.base import CommandError

        with self.assertRaises(CommandError):
            call_command("build_app", "--no-such-option")


class IsolationTests(ExecutionTestCase):
    def run_in_every_mode(self, dry_run: bool):
        hooks = [HookBinding("h", HookFamily.PRE_TOOL, _hook())]
        return DirectExecutor(self.context(dry_run=dry_run), hooks).run(
            [ToolCall("t", _ok)]
        )

    def test_no_network_access_in_normal_or_dry_run_mode(self) -> None:
        def refuse(*args, **kwargs):
            raise AssertionError("network access attempted")

        for dry_run in (False, True):
            with self.subTest(dry_run=dry_run):
                self.output = self.output.parent / f"net-{dry_run}"
                with (
                    patch.object(socket, "socket", refuse),
                    patch.object(socket, "create_connection", refuse),
                ):
                    self.assertTrue(self.run_in_every_mode(dry_run).ok)

    def test_no_provider_sdk_is_imported(self) -> None:
        code = (
            "import sys\n"
            "import django_angular3.automation.execution\n"
            "bad=[m for m in ('claude_agent_sdk','openai','google.genai','copilot')"
            " if m in sys.modules]\n"
            "sys.exit(1 if bad else 0)"
        )
        completed = subprocess.run(
            [sys.executable, "-I", "-c", code], cwd=ROOT, check=False
        )
        self.assertEqual(completed.returncode, 0)

    def test_no_credential_is_read_from_the_environment(self) -> None:
        canary = {"ANTHROPIC_API_KEY": "canary", "OPENAI_API_KEY": "canary"}
        reads = []
        real_get = os.environ.get

        def spy(key, default=None):
            reads.append(key)
            return real_get(key, default)

        for dry_run in (False, True):
            with self.subTest(dry_run=dry_run):
                self.output = self.output.parent / f"env-{dry_run}"
                with (
                    patch.dict(os.environ, canary),
                    patch.object(os.environ, "get", spy),
                ):
                    self.run_in_every_mode(dry_run)
                self.assertFalse([k for k in reads if k in canary])

    def test_a_dry_run_runs_nothing_and_writes_nothing(self) -> None:
        ran = []

        def tool(context, inputs):
            ran.append(1)
            return {}

        hooks = [HookBinding("h", HookFamily.PRE_TOOL, _hook(ValueError("no")))]
        result = DirectExecutor(self.context(dry_run=True), hooks).run(
            [ToolCall("a", tool), ToolCall("b", tool)]
        )

        self.assertEqual(ran, [])
        self.assertTrue(result.ok and result.dry_run)
        self.assertEqual(result.planned, ("a", "b"))
        self.assertFalse(self.output.exists())


class FullRunTests(ExecutionTestCase):
    def test_a_full_fake_run_against_a_generated_app_shaped_directory(self) -> None:
        app = self.output.parent / "app"
        (app / "build").mkdir(parents=True)

        def export(context, inputs):
            (app / "api.json").write_text("{}", encoding="utf-8")
            return {"destination": str(app / "api.json")}

        def schema_exists(context, observation):
            if not (app / "api.json").is_file():
                raise FileNotFoundError("api.json")

        hooks = [HookBinding("post-generation", HookFamily.POST_TOOL, schema_exists)]

        result = DirectExecutor(self.context(), hooks).run(
            [ToolCall("openapi_schema_export", export), ToolCall("build", _ok)]
        )

        self.assertTrue(result.ok)
        kinds = [e["kind"] for e in self.events()]
        self.assertEqual(kinds, ["run", "tool", "hook", "tool", "hook", "acceptance"])
        self.assertEqual(
            json.loads(json.dumps(self.events()[-1]))["decision"], "accepted"
        )


if __name__ == "__main__":
    unittest.main()
