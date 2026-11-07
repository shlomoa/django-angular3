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
