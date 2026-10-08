"""Run the resolved steps of an app build and record the evidence.

Steps run by ordered level (``exec_order``), in step order within a level, and the
run halts at the first failure. Every external process goes through
``command_execution.run_command``. The evidence names the pinned ngdj package and
the mapping versions the steps were resolved with, so a run can be reproduced.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

from . import command_execution
from .angular import AngularInvocation
from .command_translation import AppBuildStep
from .config import ProjectConfig
from .ngdj_command_mapping import CommandMapping
from .settings import AngularCommandError, DjangoAngularSettings
from .step_bridge import StepBridgeError, build_invocations, stage_document

EVIDENCE_FILE_NAME: Final = "build-evidence.json"
_OUTPUT_TAIL: Final = 4000

STATUS_SUCCEEDED: Final = "succeeded"
STATUS_FAILED: Final = "failed"
STATUS_SKIPPED: Final = "skipped"
STATUS_PENDING: Final = "pending"


@dataclass(frozen=True)
class InvocationRecord:
    """The outcome of one subprocess call of a step."""

    argv: tuple[str, ...]
    cwd: str
    returncode: int | None
    stdout: str = ""
    stderr: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "argv": list(self.argv),
            "cwd": self.cwd,
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
        }


@dataclass
class StepRecord:
    """A step with what happened to it: pending, succeeded, failed or skipped."""

    step: AppBuildStep
    status: str = STATUS_PENDING
    invocations: list[InvocationRecord] = field(default_factory=list)
    error: str | None = None


@dataclass
class ExecutionEvidence:
    """What a run (or a dry run) resolved, executed and was pinned to."""

    project_config: Path
    ngdj_package: str
    mapping_version: int | None
    openui_spec_version: str | None
    dry_run: bool
    records: list[StepRecord]

    @property
    def steps(self) -> tuple[AppBuildStep, ...]:
        return tuple(record.step for record in self.records)

    @property
    def failed(self) -> StepRecord | None:
        return next((r for r in self.records if r.status == STATUS_FAILED), None)

    def to_dict(self) -> dict[str, object]:
        return {
            "projectConfig": str(self.project_config),
            "dryRun": self.dry_run,
            "ngdj": {
                "package": self.ngdj_package,
                "mappingVersion": self.mapping_version,
                "openuiSpecVersion": self.openui_spec_version,
            },
            "steps": [step_to_dict(r.step, r) for r in self.records],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


def step_to_dict(
    step: AppBuildStep, record: StepRecord | None = None
) -> dict[str, object]:
    """Serialize a step: order, command, parameters and reason, plus its outcome."""
    result: dict[str, object] = {
        "stage": step.exec_order,
        "step": step.name_id,
        "mode": step.change_op,
        "domain": None if step.change_domain is None else step.change_domain.value,
        "target": step.change_target,
        "nodeId": step.node_id,
        "concern": step.concern_key,
        "command": step.command,
        "ngdjCommand": step.ngdj_command,
        "parameters": dict(step.parameters),
        "unresolved": list(step.unresolved),
        "reason": step.change_reason,
    }
    if record is not None and record.status != STATUS_PENDING:
        result["status"] = record.status
        result["invocations"] = [i.to_dict() for i in record.invocations]
        if record.error:
            result["error"] = record.error
    return result


def new_evidence(
    project_config: ProjectConfig,
    settings: DjangoAngularSettings,
    mapping: CommandMapping | None,
    steps: tuple[AppBuildStep, ...],
    *,
    dry_run: bool,
) -> ExecutionEvidence:
    """Evidence for steps that nothing has run yet."""
    return ExecutionEvidence(
        project_config=project_config.config_path,
        ngdj_package=settings.ng_add_package,
        mapping_version=None if mapping is None else mapping.mapping_version,
        openui_spec_version=None if mapping is None else mapping.openui_spec_version,
        dry_run=dry_run,
        records=[StepRecord(step) for step in steps],
    )


def levels(records: list[StepRecord]) -> Iterator[list[StepRecord]]:
    """Group the steps into their ordered levels: records of one ``exec_order``."""
    level: list[StepRecord] = []
    for record in records:
        if level and level[0].step.exec_order != record.step.exec_order:
            yield level
            level = []
        level.append(record)
    if level:
        yield level


def unresolved_steps(steps: tuple[AppBuildStep, ...]) -> list[str]:
    """Describe the steps that cannot run for want of a resolved option."""
    return [
        f"{step.command} for {step.change_target} needs {', '.join(step.unresolved)}"
        for step in steps
        if step.unresolved
    ]


def execute_steps(
    evidence: ExecutionEvidence,
    project_config: ProjectConfig,
    settings: DjangoAngularSettings,
) -> None:
    """Run the steps of ``evidence`` level by level, halting at the first failure.

    Each record is updated in place. After a failure the remaining steps are marked
    skipped and nothing else runs.
    """
    halted = False
    for level in levels(evidence.records):
        for record in level:
            if halted:
                record.status = STATUS_SKIPPED
                continue
            if not _run_step(record, project_config, settings):
                halted = True


def _run_step(
    record: StepRecord, project_config: ProjectConfig, settings: DjangoAngularSettings
) -> bool:
    """Run one step; ``False`` when it failed."""
    step = record.step
    try:
        if "document" in step.parameters:
            stage_document(project_config)
        invocations = build_invocations(step, project_config, settings)
    except (StepBridgeError, AngularCommandError, OSError) as exc:
        return _fail(record, str(exc))
    for invocation in invocations:
        outcome = _run_invocation(invocation)
        record.invocations.append(outcome)
        if outcome.returncode != 0:
            return _fail(record, _failure_message(step, outcome))
    record.status = STATUS_SUCCEEDED
    return True


def _run_invocation(invocation: AngularInvocation) -> InvocationRecord:
    cwd = str(invocation.cwd)
    try:
        result = command_execution.run_command(
            invocation.argv, cwd=invocation.cwd, check=False
        )
    except (command_execution.CommandExecutionError, OSError) as exc:
        return InvocationRecord(invocation.argv, cwd, None, stderr=str(exc))
    return InvocationRecord(
        invocation.argv,
        cwd,
        result.returncode,
        stdout=result.stdout[-_OUTPUT_TAIL:],
        stderr=result.stderr[-_OUTPUT_TAIL:],
    )


def _failure_message(step: AppBuildStep, outcome: InvocationRecord) -> str:
    code = (
        "did not start"
        if outcome.returncode is None
        else (f"exited with {outcome.returncode}")
    )
    message = f"'{' '.join(outcome.argv)}' {code}."
    detail = outcome.stderr.strip()
    return f"{message}\n{detail}" if detail else message


def _fail(record: StepRecord, message: str) -> bool:
    record.status = STATUS_FAILED
    record.error = message
    return False


def write_evidence(evidence: ExecutionEvidence, output: Path) -> Path:
    """Write the evidence of a real run to ``<output>/build-evidence.json``."""
    output.mkdir(parents=True, exist_ok=True)
    path = output / EVIDENCE_FILE_NAME
    path.write_text(evidence.to_json() + "\n", encoding="utf-8")
    return path
