"""Generate ``tests/fixtures/automation``: golden serialization of each contract.

Produced by the code under test, reviewed in the PR, never edited by hand::

    python -m tests.generate_automation_goldens
"""

import json
import tempfile
from pathlib import Path

from django_angular3.automation.evidence import (
    EVIDENCE_FILE_NAME,
    JsonLinesEvidenceRecorder,
)
from tests.automation_samples import (
    SAMPLES,
    execution_scenarios,
    fake_run_events,
    fixed_clock,
)

GOLDEN_DIR = Path(__file__).resolve().parent / "fixtures" / "automation"


def main() -> None:
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    for name, sample in SAMPLES.items():
        (GOLDEN_DIR / f"{name}.json").write_text(
            sample.to_json() + "\n", encoding="utf-8", newline="\n"
        )
    with tempfile.TemporaryDirectory() as directory:
        recorder = JsonLinesEvidenceRecorder(Path(directory), "run-1", fixed_clock())
        for kind, payload in fake_run_events():
            recorder.record(kind, payload)
        (GOLDEN_DIR / "evidence-stream.jsonl").write_bytes(
            (Path(directory) / EVIDENCE_FILE_NAME).read_bytes()
        )

    from django_angular3.automation.execution import DirectExecutor, ExecutionContext

    for name, (calls, hooks) in execution_scenarios().items():
        with tempfile.TemporaryDirectory() as directory:
            recorder = JsonLinesEvidenceRecorder(
                Path(directory), "run-1", fixed_clock()
            )
            context = ExecutionContext(None, Path(directory), "run-1", recorder)
            DirectExecutor(context, hooks).run(calls)
            (GOLDEN_DIR / f"{name}.jsonl").write_bytes(
                (Path(directory) / EVIDENCE_FILE_NAME).read_bytes()
            )

    from tests.test_automation_hooks import hook_log_goldens, setUpModule

    setUpModule()
    for name, text in hook_log_goldens().items():
        (GOLDEN_DIR / name).write_text(text, encoding="utf-8", newline="\n")

    from django_angular3.automation.tool_catalog import CATALOG

    catalog = {
        name: {
            "inputs": [
                {"name": i.name, "required": i.required, "kind": i.kind}
                for i in spec.inputs
            ],
            "outputs": list(spec.outputs),
            "implementation": spec.implementation,
        }
        for name, spec in sorted(CATALOG.items())
    }
    (GOLDEN_DIR / "tool-catalog.json").write_text(
        json.dumps(catalog, indent=2) + "\n", encoding="utf-8", newline="\n"
    )


if __name__ == "__main__":
    main()
