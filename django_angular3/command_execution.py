"""Single owner of external command execution.

Every external process started by django-angular3 goes through this module.
Two execution modes are provided: sequential and multithreaded.
"""

from __future__ import annotations

import logging
import subprocess
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import NamedTuple, Protocol

logger = logging.getLogger(__name__)

DEFAULT_MAX_WORKERS = 4


class CommandExecutionError(RuntimeError):
    """Raised when an external command cannot be started or exits non-zero."""


class RawCommand(Protocol):
    """Anything with an argument vector and a working directory."""

    @property
    def argv(self) -> Sequence[str]: ...

    @property
    def cwd(self) -> Path: ...


class CommandResult(NamedTuple):
    """Captured outcome of a finished external command."""

    returncode: int
    stdout: str
    stderr: str


def run_command(
    argv: Sequence[str], *, cwd: Path | None = None, check: bool = True
) -> CommandResult:
    """Run one command, capturing stdout and stderr.

    The captured output is always returned; callers may ignore it. With
    ``check`` true a non-zero exit raises ``CommandExecutionError`` carrying the
    command's stderr; with ``check`` false the result is returned as is.
    """
    logger.debug("Running %s in %s", " ".join(argv), cwd)
    try:
        completed = subprocess.run(
            list(argv),
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise CommandExecutionError(f"Command not found: {argv[0]}") from exc

    result = CommandResult(
        completed.returncode, completed.stdout or "", completed.stderr or ""
    )
    if result.stdout.strip():
        logger.debug("stdout of %s:\n%s", " ".join(argv), result.stdout.strip())
    if result.stderr.strip():
        logger.debug("stderr of %s:\n%s", " ".join(argv), result.stderr.strip())
    if check and result.returncode:
        message = (
            f"Command '{' '.join(argv)}' failed with exit code {result.returncode}."
        )
        if result.stderr.strip():
            message = f"{message}\n{result.stderr.strip()}"
        raise CommandExecutionError(message)
    return result


def execute_sequential(commands: Sequence[RawCommand]) -> list[CommandResult]:
    """Run commands one after another, stopping at the first failure."""
    return [run_command(command.argv, cwd=command.cwd) for command in commands]


def execute_parallel(
    commands: Sequence[RawCommand], *, max_workers: int = DEFAULT_MAX_WORKERS
) -> list[CommandResult]:
    """Run commands concurrently in a fixed-size thread pool.

    Results are returned in input order. Every command is allowed to finish;
    failures are then raised together as one ``CommandExecutionError``.
    """
    if not commands:
        return []
    workers = max(1, min(max_workers, len(commands)))
    logger.debug("Executing %d commands with %d workers", len(commands), workers)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [
            pool.submit(run_command, command.argv, cwd=command.cwd)
            for command in commands
        ]
    errors = [f.exception() for f in futures if f.exception() is not None]
    if errors:
        raise CommandExecutionError("; ".join(str(e) for e in errors)) from errors[0]
    return [f.result() for f in futures]


def execute(
    commands: Sequence[RawCommand],
    *,
    parallel: bool = False,
    max_workers: int = DEFAULT_MAX_WORKERS,
) -> list[CommandResult]:
    """Run commands in the selected mode: sequential (default) or parallel."""
    if parallel:
        return execute_parallel(commands, max_workers=max_workers)
    return execute_sequential(commands)
