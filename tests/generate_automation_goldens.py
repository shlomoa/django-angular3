"""Generate ``tests/fixtures/automation``: golden serialization of each contract.

Produced by the code under test, reviewed in the PR, never edited by hand::

    python -m tests.generate_automation_goldens
"""

import tempfile
from pathlib import Path

from django_angular3.automation.evidence import (
    EVIDENCE_FILE_NAME,
    JsonLinesEvidenceRecorder,
)
from tests.automation_samples import SAMPLES, fake_run_events, fixed_clock

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


if __name__ == "__main__":
    main()
