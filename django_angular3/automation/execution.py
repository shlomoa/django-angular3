"""Synchronous provider-neutral direct execution (AIR-4, AIR-5, FR-8).

The controller runs Tools in order and applies the Hook boundaries around them:

* a failing pre-tool Hook **blocks** its Tool, which never runs;
* a failing post-tool Hook **halts** the run and suppresses dependent Tools;
* a failing session-stop Hook only **warns**: the decided result is unchanged.

Expected failures (``CommandExecutionError``, ``ContractError``) and unexpected
exceptions inside a Tool or Hook are normalized into structured failures and
recorded; nothing propagates raw. Every outcome goes to the injected evidence
recorder in execution order. A dry run resolves the selection and returns it: no
Tool, Hook, adapter, recorder write, credential lookup or network access happens.

Process execution stays with ``command_execution``: :func:`command_tool` builds a
Tool that starts its process only through ``command_execution.run_command``, so the
controller adds no second subprocess path. Provider SDKs are never imported here.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .. import command_execution
from .contracts import (
    AutomationFailure,
    Consequence,
    ContractError,
    FailureCategory,
    HookFamily,
    HookOutcome,
    ToolResult,
)
from .evidence import (
    KIND_ACCEPTANCE,
    KIND_HOOK,
    KIND_RUN,
    KIND_TOOL,
    EvidenceRecorder,
    NoOpEvidenceRecorder,
)

#: A Tool: structured inputs in, structured output (a mapping) out. It raises on
#: failure; the controller normalizes what it raises.
ToolFunction = Callable[["ExecutionContext", Mapping[str, Any]], Mapping[str, Any]]
#: A Hook: observes a Tool call and returns normally when it passes, raises when
#: it fails.
HookFunction = Callable[["ExecutionContext", "HookObservation"], None]


@dataclass(frozen=True)
class ExecutionContext:
    """What a run needs, injected at the execution boundary."""

    project_config: Any
    output_dir: Path
    run_id: str
    recorder: EvidenceRecorder = field(default_factory=NoOpEvidenceRecorder)
    dry_run: bool = False
    acknowledged: bool = False


@dataclass(frozen=True)
class ToolCall:
    """One Tool invocation of the run, by canonical Tool name."""

    tool: str
    function: ToolFunction
    inputs: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class HookBinding:
    """A Hook bound to a lifecycle family and, for tool families, a Tool scope."""

    name: str
    family: HookFamily
    function: HookFunction
    #: Tool names the Hook wraps; ``None`` matches every Tool. Ignored for
    #: session-stop.
    tools: frozenset[str] | None = None

    def applies_to(self, tool: str) -> bool:
        return self.tools is None or tool in self.tools


@dataclass(frozen=True)
class HookObservation:
    """What a Hook is shown: the canonical Tool identity and, after it, its result."""

    family: HookFamily
    tool: str | None
    inputs: Mapping[str, Any]
    result: ToolResult | None = None


@dataclass(frozen=True)
class StepOutcome:
    """The outcome of one Tool call with its Hooks."""

    tool: str
    status: str  # "succeeded", "failed", "blocked" or "skipped"
    result: ToolResult | None
    hooks: tuple[HookOutcome, ...] = ()


@dataclass(frozen=True)
class RunResult:
    """The decided outcome of a run."""

    ok: bool
    failure: AutomationFailure | None
    steps: tuple[StepOutcome, ...]
    warnings: tuple[AutomationFailure, ...] = ()
    dry_run: bool = False

    @property
    def planned(self) -> tuple[str, ...]:
        """The Tool names, in order, for a dry run."""
        return tuple(step.tool for step in self.steps)


def command_tool(
    argv_of: Callable[[Mapping[str, Any]], Sequence[str]],
    cwd_of: Callable[[ExecutionContext], Path] | None = None,
) -> ToolFunction:
    """A Tool that runs one external command through ``command_execution``."""

    def run(context: ExecutionContext, inputs: Mapping[str, Any]) -> Mapping[str, Any]:
        cwd = None if cwd_of is None else cwd_of(context)
        result = command_execution.run_command(argv_of(inputs), cwd=cwd)
        return {"stdout": result.stdout, "stderr": result.stderr}

    return run


class DirectExecutor:
    """Runs Tool calls in order with the Hook boundaries of the canonical contracts."""

    def __init__(
        self, context: ExecutionContext, hooks: Sequence[HookBinding] = ()
    ) -> None:
        self._context = context
        self._hooks = tuple(hooks)

    def run(self, calls: Sequence[ToolCall]) -> RunResult:
        context = self._context
        if context.dry_run:
            # Resolve the selection only: nothing runs, nothing is recorded.
            steps = tuple(StepOutcome(call.tool, "skipped", None) for call in calls)
            return RunResult(True, None, steps, dry_run=True)

        failure = self._record(KIND_RUN, {"dry_run": False, "tools": len(calls)})
        steps: list[StepOutcome] = []
        stopped = failure
        for call in calls:
            if stopped is not None:
                steps.append(StepOutcome(call.tool, "skipped", None))
                continue
            outcome = self._run_call(call)
            steps.append(outcome)
            stopped = self._stop_failure(outcome)
            if stopped is None and outcome.status == "failed":
                stopped = outcome.result.failure if outcome.result else None
        failure = stopped

        warnings = self._session_stop()
        accepted = failure is None
        evidence_failure = self._record(
            KIND_ACCEPTANCE,
            {
                "decision": "accepted" if accepted else "rejected",
                "failure": None if failure is None else failure.to_dict(),
                "warnings": len(warnings),
            },
        )
        if failure is None:
            failure = evidence_failure
        return RunResult(
            failure is None, failure, tuple(steps), tuple(warnings), dry_run=False
        )

    # -- Tool calls and Hooks ------------------------------------------------

    def _run_call(self, call: ToolCall) -> StepOutcome:
        hook_outcomes: list[HookOutcome] = []
        for hook in self._tool_hooks(HookFamily.PRE_TOOL, call.tool):
            outcome = self._run_hook(
                hook, HookObservation(HookFamily.PRE_TOOL, call.tool, call.inputs)
            )
            hook_outcomes.append(outcome)
            if not outcome.ok:
                return StepOutcome(call.tool, "blocked", None, tuple(hook_outcomes))

        result = self._run_tool(call)
        status = "succeeded" if result.ok else "failed"
        if result.ok:
            for hook in self._tool_hooks(HookFamily.POST_TOOL, call.tool):
                outcome = self._run_hook(
                    hook,
                    HookObservation(
                        HookFamily.POST_TOOL, call.tool, call.inputs, result
                    ),
                )
                hook_outcomes.append(outcome)
                if not outcome.ok:
                    status = "failed"
                    break
        return StepOutcome(call.tool, status, result, tuple(hook_outcomes))

    def _stop_failure(self, outcome: StepOutcome) -> AutomationFailure | None:
        """The failure that stops the run after ``outcome``, if any."""
        for hook in outcome.hooks:
            if not hook.ok and hook.consequence in (
                Consequence.BLOCK,
                Consequence.HALT,
            ):
                return hook.failure
        if outcome.status == "failed" and outcome.result is not None:
            return outcome.result.failure
        return None

    def _run_tool(self, call: ToolCall) -> ToolResult:
        try:
            output = call.function(self._context, call.inputs)
            result = ToolResult(call.tool, output if output is not None else {})
        except Exception as exc:  # noqa: BLE001 - normalized below, never raw
            result = ToolResult(call.tool, {}, _normalize(exc))
        recorded = self._record(
            KIND_TOOL,
            {
                "name": call.tool,
                "ok": result.ok,
                "output": result.output,
                "failure": None if result.failure is None else result.failure.to_dict(),
            },
        )
        if recorded is not None and result.ok:
            return ToolResult(call.tool, {}, recorded)
        return result

    def _run_hook(self, hook: HookBinding, observation: HookObservation) -> HookOutcome:
        try:
            hook.function(self._context, observation)
            outcome = HookOutcome(hook.name, hook.family)
        except Exception as exc:  # noqa: BLE001 - normalized below, never raw
            failure = _normalize(exc, hook_name=hook.name)
            outcome = HookOutcome(hook.name, hook.family, failure)
        recorded = self._record(
            KIND_HOOK,
            {
                "name": hook.name,
                "family": hook.family.value,
                "tool": observation.tool,
                "ok": outcome.ok,
                "consequence": None
                if outcome.consequence is None
                else outcome.consequence.value,
                "failure": None
                if outcome.failure is None
                else outcome.failure.to_dict(),
            },
        )
        if recorded is not None and outcome.ok:
            return HookOutcome(hook.name, hook.family, recorded)
        return outcome

    def _session_stop(self) -> list[AutomationFailure]:
        """Run the session-stop Hooks; their failures are warnings only."""
        warnings: list[AutomationFailure] = []
        for hook in self._hooks:
            if hook.family is not HookFamily.SESSION_STOP:
                continue
            outcome = self._run_hook(
                hook, HookObservation(HookFamily.SESSION_STOP, None, {})
            )
            if not outcome.ok and outcome.failure is not None:
                warnings.append(outcome.failure)
        return warnings

    def _tool_hooks(self, family: HookFamily, tool: str) -> list[HookBinding]:
        return [h for h in self._hooks if h.family is family and h.applies_to(tool)]

    def _record(
        self, kind: str, payload: Mapping[str, Any]
    ) -> AutomationFailure | None:
        """Record an event; a recorder failure is returned, never swallowed."""
        try:
            self._context.recorder.record(kind, payload)
        except ContractError as exc:
            return exc.to_failure()
        except Exception as exc:  # noqa: BLE001
            return _normalize(exc)
        return None


def _normalize(exc: BaseException, hook_name: str | None = None) -> AutomationFailure:
    """A structured failure for an exception raised by a Tool, Hook or recorder."""
    if isinstance(exc, ContractError):
        return exc.to_failure()
    details: dict[str, Any] = {"exception": type(exc).__name__}
    if hook_name is not None:
        details["hook"] = hook_name
    message = str(exc) or type(exc).__name__
    if isinstance(exc, command_execution.CommandExecutionError):
        return AutomationFailure(FailureCategory.EXTERNAL_TOOL_FAILED, message, details)
    if hook_name is not None:
        return AutomationFailure(FailureCategory.HOOK_FAILED, message, details)
    return AutomationFailure(FailureCategory.UNEXPECTED, message, details)
