"""Sample contracts for the automation tests and their generated golden files.

``python -m tests.generate_automation_goldens`` serializes these with the code
under test into ``tests/fixtures/automation/``; the files are never edited by hand.
"""

from django_angular3.automation.contracts import (
    AdapterResult,
    AdapterStatus,
    AutomationFailure,
    FailureCategory,
    HookFamily,
    HookOutcome,
    ToolResult,
)

FAILURE = AutomationFailure(
    FailureCategory.EXTERNAL_TOOL_FAILED,
    "oasdiff exited with status 2",
    {"exit_code": 2, "tool": "oasdiff_diff"},
)

SAMPLES = {
    "failure": FAILURE,
    "tool-result-ok": ToolResult(
        "openapi_schema_export",
        {"destination": "/app/api.json", "format": "json", "schema_changed": True},
    ),
    "tool-result-failed": ToolResult("oasdiff_diff", {}, FAILURE),
    "hook-outcome-ok": HookOutcome("pre-construction", HookFamily.PRE_TOOL),
    "hook-outcome-halt": HookOutcome("post-generation", HookFamily.POST_TOOL, FAILURE),
    "adapter-result": AdapterResult(
        AdapterStatus.ACCEPTED, {"criteria": ["built", "typed"], "session": "s-1"}
    ),
}


def fake_run_events() -> list[tuple[str, dict]]:
    """A fake run: a run record, Tool, Hook and acceptance events in order."""
    return [
        ("run", {"project": "shop", "dry_run": False}),
        ("hook", {"name": "pre-construction", "family": "pre-tool", "ok": True}),
        ("tool", {"name": "openapi_schema_export", "ok": True, "output": {"n": 1}}),
        ("hook", {"name": "post-generation", "family": "post-tool", "ok": True}),
        ("acceptance", {"decision": "accepted", "criteria": ["built", "typed"]}),
    ]


def fixed_clock():
    """A deterministic injected clock: one second per call."""
    ticks = iter(range(1, 1000))
    return lambda: f"2026-01-01T00:00:{next(ticks):02d}Z"
