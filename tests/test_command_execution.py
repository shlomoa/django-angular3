"""Tests for command_execution: the single owner of external processes."""

import subprocess
import threading
import unittest
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

from django_angular3 import command_execution
from django_angular3.command_execution import (
    CommandExecutionError,
    execute,
    execute_parallel,
    execute_sequential,
    run_command,
)


@dataclass(frozen=True)
class _Cmd:
    argv: tuple[str, ...]
    cwd: Path = Path(".")


def _completed(returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess([], returncode, stdout, stderr)


class RunCommandTests(unittest.TestCase):
    def test_captures_stdout_and_stderr_in_requested_directory(self) -> None:
        with patch("django_angular3.command_execution.subprocess.run") as run:
            run.return_value = _completed(0, "out", "err")
            result = run_command(["tool", "arg"], cwd=Path("workspace"))

        run.assert_called_once_with(
            ["tool", "arg"],
            cwd=Path("workspace"),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            (result.returncode, result.stdout, result.stderr), (0, "out", "err")
        )

    def test_non_zero_exit_raises_with_stderr(self) -> None:
        with (
            patch(
                "django_angular3.command_execution.subprocess.run",
                return_value=_completed(2, "", "boom"),
            ),
            self.assertRaisesRegex(CommandExecutionError, r"exit code 2\.\nboom"),
        ):
            run_command(["tool"])

    def test_check_false_returns_failed_result(self) -> None:
        with patch(
            "django_angular3.command_execution.subprocess.run",
            return_value=_completed(3, "o", "e"),
        ):
            result = run_command(["tool"], check=False)

        self.assertEqual(result.returncode, 3)

    def test_missing_command_is_normalized(self) -> None:
        with (
            patch(
                "django_angular3.command_execution.subprocess.run",
                side_effect=FileNotFoundError,
            ),
            self.assertRaisesRegex(CommandExecutionError, "Command not found: tool"),
        ):
            run_command(["tool"])


class SequentialTests(unittest.TestCase):
    def test_runs_in_order_and_stops_at_first_failure(self) -> None:
        seen: list[str] = []

        def fake(argv, **_):
            seen.append(argv[0])
            return _completed(1 if argv[0] == "bad" else 0)

        commands = [_Cmd(("a",)), _Cmd(("bad",)), _Cmd(("c",))]
        with (
            patch("django_angular3.command_execution.subprocess.run", fake),
            self.assertRaises(CommandExecutionError),
        ):
            execute_sequential(commands)

        self.assertEqual(seen, ["a", "bad"])


class ParallelTests(unittest.TestCase):
    def test_runs_every_command_and_keeps_input_order(self) -> None:
        def fake(argv, **_):
            return _completed(0, argv[0])

        commands = [_Cmd((f"cmd{i}",)) for i in range(6)]
        with patch("django_angular3.command_execution.subprocess.run", fake):
            results = execute_parallel(commands)

        self.assertEqual([r.stdout for r in results], [f"cmd{i}" for i in range(6)])

    def test_empty_list_does_nothing(self) -> None:
        with patch("django_angular3.command_execution.subprocess.run") as run:
            self.assertEqual(execute_parallel([]), [])

        run.assert_not_called()

    def test_commands_run_concurrently(self) -> None:
        barrier = threading.Barrier(3, timeout=5)

        def fake(argv, **_):
            barrier.wait()
            return _completed()

        with patch("django_angular3.command_execution.subprocess.run", fake):
            execute_parallel([_Cmd((f"c{i}",)) for i in range(3)], max_workers=3)

    def test_pool_size_is_bounded_by_max_workers(self) -> None:
        active = 0
        peak = 0
        lock = threading.Lock()

        def fake(argv, **_):
            nonlocal active, peak
            with lock:
                active += 1
                peak = max(peak, active)
            threading.Event().wait(0.05)
            with lock:
                active -= 1
            return _completed()

        with patch("django_angular3.command_execution.subprocess.run", fake):
            execute_parallel([_Cmd((f"c{i}",)) for i in range(8)], max_workers=2)

        self.assertLessEqual(peak, 2)

    def test_failures_are_aggregated_after_all_commands_finish(self) -> None:
        completed: list[str] = []
        lock = threading.Lock()

        def fake(argv, **_):
            name = argv[0]
            if name.startswith("bad"):
                return _completed(1, "", f"{name} failed")
            with lock:
                completed.append(name)
            return _completed()

        commands = [_Cmd((n,)) for n in ("ok1", "bad1", "ok2", "bad2")]
        with (
            patch("django_angular3.command_execution.subprocess.run", fake),
            self.assertRaises(CommandExecutionError) as raised,
        ):
            execute_parallel(commands)

        self.assertIn("bad1 failed", str(raised.exception))
        self.assertIn("bad2 failed", str(raised.exception))
        self.assertCountEqual(completed, ["ok1", "ok2"])


class ModeSelectionTests(unittest.TestCase):
    def test_default_is_sequential(self) -> None:
        with (
            patch.object(command_execution, "execute_sequential") as seq,
            patch.object(command_execution, "execute_parallel") as par,
        ):
            execute([])

        seq.assert_called_once()
        par.assert_not_called()

    def test_parallel_flag_selects_parallel(self) -> None:
        with (
            patch.object(command_execution, "execute_sequential") as seq,
            patch.object(command_execution, "execute_parallel") as par,
        ):
            execute([], parallel=True, max_workers=3)

        par.assert_called_once_with([], max_workers=3)
        seq.assert_not_called()


if __name__ == "__main__":
    unittest.main()
