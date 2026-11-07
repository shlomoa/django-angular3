"""Focused command-boundary tests of build_app: determinism, ordering and exit codes.

Credential-free: the Angular CLI is a stand-in executable, and nothing here needs a
provider, a network or an installed ``oasdiff``. The halt-on-failure, dependency-skip,
evidence and dry-run cases are in ``tests/test_step_execution.py``; this module adds
the byte-for-byte determinism of the derived commands, the exit-code mapping, the
dependency order of the levels, the absence of provider imports in a dry run, and the
time bound of the derivation.
"""

import io
import json
import os
import sys
import time
import unittest
from unittest.mock import patch

from django.core.management import load_command_class
from django.core.management.base import OutputWrapper

from django_angular3.management.commands.build_app import ChangeDetector
from tests.test_step_execution import EVIDENCE_FILE_NAME, _Project
from tests.tool_config import use_tool_configuration_template

PROVIDER_MODULES = ("claude_agent_sdk", "openai", "google.genai", "copilot")


def setUpModule() -> None:
    use_tool_configuration_template()


class CommandBoundaryTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.project = _Project(self)

    def dry_run(self) -> str:
        return self.project.run_build(self.project.change_set(), dry_run=True)

    def run_from_argv(self, *extra: str) -> int:
        """The exit code of ``manage.py build_app``, as the command line sees it."""
        command = load_command_class("django_angular3", "build_app")
        command.stdout = OutputWrapper(io.StringIO())
        command.stderr = OutputWrapper(io.StringIO())
        argv = [
            "manage.py",
            "build_app",
            f"--current-config={self.project.project_config.config_path}",
            f"--previous-config={self.project.previous.project_config.config_path}",
            f"--output={self.project.root / 'build'}",
            *extra,
        ]
        change_set = self.project.change_set()
        with (
            patch.object(ChangeDetector, "detect_changes", return_value=change_set),
            patch(
                "django_angular3.management.commands.build_app.load_angular_settings",
                return_value=self.project.settings,
            ),
            patch("sys.stdout", io.StringIO()),
            patch("sys.stderr", io.StringIO()),
            self.assertRaises(SystemExit) as exit_info,
        ):
            command.run_from_argv(argv)
            raise SystemExit(0)
        return int(exit_info.exception.code or 0)


class DeterminismTests(CommandBoundaryTestCase):
    def test_identical_inputs_give_byte_identical_dry_runs(self) -> None:
        first = self.dry_run()

        for _ in range(3):
            self.assertEqual(self.dry_run().encode("utf-8"), first.encode("utf-8"))

    def test_identical_inputs_give_byte_identical_evidence(self) -> None:
        self.project.run_build(self.project.change_set())
        path = self.project.root / "build" / EVIDENCE_FILE_NAME
        first = path.read_bytes()
        path.unlink()
        self.project.log.write_text("", encoding="utf-8")

        self.project.run_build(self.project.change_set())

        self.assertEqual(path.read_bytes(), first)


class OrderTests(CommandBoundaryTestCase):
    def test_the_levels_never_decrease_and_the_gate_comes_last(self) -> None:
        steps = json.loads(self.dry_run())["steps"]

        stages = [step["stage"] for step in steps]
        self.assertEqual(stages, sorted(stages))
        self.assertEqual(steps[-1]["step"], "last-check")
        names = [step["step"] for step in steps]
        self.assertLess(
            names.index("angular-workspace-foundation"),
            names.index("angular-app-composition"),
        )
        self.assertLess(
            names.index("angular-app-composition"), names.index("ngdj_add_page")
        )

    def test_the_real_run_calls_follow_the_dry_run_order(self) -> None:
        planned = [s["command"] for s in json.loads(self.dry_run())["steps"]]

        self.project.run_build(self.project.change_set())

        evidence = json.loads(
            (self.project.root / "build" / EVIDENCE_FILE_NAME).read_text("utf-8")
        )
        self.assertEqual([s["command"] for s in evidence["steps"]], planned)


class ExitCodeTests(CommandBoundaryTestCase):
    def test_success_and_dry_run_exit_zero(self) -> None:
        self.assertEqual(self.run_from_argv("--dry-run"), 0)
        self.assertEqual(self.run_from_argv(), 0)

    def test_a_failing_step_exits_non_zero_and_stops_the_run(self) -> None:
        with patch.dict(os.environ, {"FAKE_NG_FAIL": "angular-django2:material-app"}):
            code = self.run_from_argv()

        self.assertNotEqual(code, 0)
        calls = self.project.calls()
        self.assertNotIn("build", [c[0] for c in calls])
        evidence = json.loads(
            (self.project.root / "build" / EVIDENCE_FILE_NAME).read_text("utf-8")
        )
        failed = [s for s in evidence["steps"] if s["status"] == "failed"]
        self.assertEqual([s["step"] for s in failed], ["angular-app-composition"])
        self.assertIn("simulated ng failure", failed[0]["error"])

    def test_an_unknown_option_exits_non_zero(self) -> None:
        self.assertNotEqual(self.run_from_argv("--no-such-option"), 0)


class IsolationTests(CommandBoundaryTestCase):
    def test_a_dry_run_imports_no_provider_sdk_and_reads_no_credentials(self) -> None:
        before = {m for m in PROVIDER_MODULES if m in sys.modules}
        canary = {"ANTHROPIC_API_KEY": "canary", "OPENAI_API_KEY": "canary"}
        reads: list[str] = []
        real_get = os.environ.get

        def spy(key, default=None):
            reads.append(key)
            return real_get(key, default)

        with patch.dict(os.environ, canary), patch.object(os.environ, "get", spy):
            self.dry_run()

        after = {m for m in PROVIDER_MODULES if m in sys.modules}
        self.assertEqual(after, before)
        self.assertFalse([key for key in reads if key in canary])


class PerformanceTests(CommandBoundaryTestCase):
    def test_deriving_and_translating_stays_far_under_thirty_seconds(self) -> None:
        started = time.monotonic()
        self.dry_run()
        self.assertLess(time.monotonic() - started, 30)


if __name__ == "__main__":
    unittest.main()
