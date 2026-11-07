"""Generate ``tests/fixtures/automation``: golden serialization of each contract.

Produced by the code under test, reviewed in the PR, never edited by hand::

    python -m tests.generate_automation_goldens
"""

from pathlib import Path

from tests.automation_samples import SAMPLES

GOLDEN_DIR = Path(__file__).resolve().parent / "fixtures" / "automation"


def main() -> None:
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    for name, sample in SAMPLES.items():
        (GOLDEN_DIR / f"{name}.json").write_text(
            sample.to_json() + "\n", encoding="utf-8", newline="\n"
        )


if __name__ == "__main__":
    main()
