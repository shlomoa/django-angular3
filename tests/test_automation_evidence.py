"""Credential-free tests of the durable evidence recorder."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from django_angular3.automation.contracts import ContractError, FailureCategory
from django_angular3.automation.evidence import (
    EVIDENCE_FILE_NAME,
    JsonLinesEvidenceRecorder,
    NoOpEvidenceRecorder,
    read_events,
)
from tests.automation_samples import fake_run_events, fixed_clock
from tests.generate_automation_goldens import GOLDEN_DIR
from tests.workspace_temp import WORKSPACE_TEMP_DIR

CANARIES = ("sk-live-CANARY", "cookie-CANARY", "bearer-CANARY", "native-CANARY")


class EvidenceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(dir=WORKSPACE_TEMP_DIR)
        self.addCleanup(temporary.cleanup)
        self.output = Path(temporary.name) / "build"
        self.path = self.output / EVIDENCE_FILE_NAME

    def recorder(self, run_id: str = "run-1") -> JsonLinesEvidenceRecorder:
        return JsonLinesEvidenceRecorder(self.output, run_id, fixed_clock())

    def record_fake_run(self, recorder) -> None:
        for kind, payload in fake_run_events():
            recorder.record(kind, payload)


class StreamTests(EvidenceTestCase):
    def test_every_line_is_utf8_json_in_order(self) -> None:
        self.record_fake_run(self.recorder())

        lines = self.path.read_text(encoding="utf-8").splitlines()
        events = [json.loads(line) for line in lines]
        self.assertEqual(
            [e["kind"] for e in events],
            ["run", "hook", "tool", "hook", "acceptance"],
        )
        self.assertEqual([e["seq"] for e in events], [1, 2, 3, 4, 5])
        self.assertTrue(all(e["run_id"] == "run-1" for e in events))

    def test_events_are_flushed_as_they_complete(self) -> None:
        recorder = self.recorder()
        recorder.record("run", {"project": "shop"})
        self.assertEqual(len(read_events(self.path).events), 1)
        recorder.record("tool", {"name": "t", "ok": False})
        # Nothing more is recorded: the run halted. The file is still inspectable.
        self.assertEqual(len(read_events(self.path).events), 2)

    def test_identical_injected_values_give_identical_bytes(self) -> None:
        self.record_fake_run(self.recorder())
        first = self.path.read_bytes()
        self.path.unlink()

        self.record_fake_run(self.recorder())

        self.assertEqual(self.path.read_bytes(), first)

    def test_the_stream_matches_the_generated_golden_byte_for_byte(self) -> None:
        self.record_fake_run(self.recorder())

        golden = (GOLDEN_DIR / "evidence-stream.jsonl").read_bytes()
        self.assertEqual(self.path.read_bytes(), golden)

    def test_the_noop_recorder_writes_nothing(self) -> None:
        self.record_fake_run(NoOpEvidenceRecorder())

        self.assertFalse(self.output.exists())

    def test_invalid_events_are_refused(self) -> None:
        recorder = self.recorder()
        for kind, payload in (
            ("nope", {}),
            ("tool", {"seq": 9}),
            ("tool", {"timestamp": "x"}),
            ("tool", {"x": object()}),
        ):
            with self.subTest(kind=kind, payload=payload):
                with self.assertRaises(ContractError) as ctx:
                    recorder.record(kind, payload)
                self.assertEqual(ctx.exception.category, FailureCategory.INVALID_INPUT)
        self.assertFalse(self.path.exists())

    def test_an_empty_run_id_is_refused(self) -> None:
        with self.assertRaises(ContractError):
            JsonLinesEvidenceRecorder(self.output, "", fixed_clock())


class FailureTests(EvidenceTestCase):
    def test_a_failing_writer_is_a_structured_failure_not_a_silent_drop(self) -> None:
        recorder = self.recorder()
        with (
            patch("pathlib.Path.open", side_effect=OSError(28, "No space left")),
            self.assertRaises(ContractError) as ctx,
        ):
            recorder.record("tool", {"name": "t"})
        failure = ctx.exception.to_failure()
        self.assertEqual(failure.category, FailureCategory.EVIDENCE_WRITE_FAILED)
        self.assertIn("No space left", failure.message)

    def test_an_unwritable_output_directory_is_a_structured_failure(self) -> None:
        blocker = self.output.parent / "blocker"
        blocker.write_text("a file, not a directory", encoding="utf-8")
        recorder = JsonLinesEvidenceRecorder(blocker / "build", "r", fixed_clock())

        with self.assertRaises(ContractError) as ctx:
            recorder.record("run", {})
        self.assertEqual(ctx.exception.category, FailureCategory.EVIDENCE_WRITE_FAILED)

    def test_a_failed_write_does_not_consume_a_sequence_number(self) -> None:
        recorder = self.recorder()
        with patch("pathlib.Path.open", side_effect=OSError("boom")):
            with self.assertRaises(ContractError):
                recorder.record("run", {})
        recorder.record("run", {})
        self.assertEqual(read_events(self.path).events[0]["seq"], 1)


class SecretTests(EvidenceTestCase):
    def test_secret_canaries_never_reach_the_written_bytes(self) -> None:
        recorder = self.recorder()
        recorder.record(
            "tool",
            {
                "name": "t",
                "api_key": CANARIES[0],
                "headers": {"Cookie": CANARIES[1], "Authorization": CANARIES[2]},
                "output": f"called with Bearer {CANARIES[2]}",
            },
        )
        with self.assertRaises(ContractError) as ctx:
            recorder.record("tool", {"name": "t", "raw_response": CANARIES[3]})
        self.assertEqual(ctx.exception.category, FailureCategory.EVIDENCE_REJECTED)

        data = self.path.read_bytes().decode("utf-8")
        for canary in CANARIES:
            self.assertNotIn(canary, data)
        self.assertEqual(len(read_events(self.path).events), 1)

    def test_every_artifact_of_the_test_directory_is_free_of_canaries(self) -> None:
        recorder = self.recorder()
        recorder.record("tool", {"name": "t", "token": CANARIES[0]})
        for root, _, files in os.walk(self.output.parent):
            for name in files:
                data = (Path(root) / name).read_bytes().decode("utf-8", "replace")
                self.assertNotIn(CANARIES[0], data)


class PriorEventTests(EvidenceTestCase):
    def write_prior(self, text: str) -> None:
        self.output.mkdir(parents=True)
        self.path.write_text(text, encoding="utf-8")

    def test_malformed_prior_lines_are_reported_and_kept(self) -> None:
        good = '{"kind":"run","run_id":"old","seq":1,"timestamp":"t"}'
        prior = f'{good}\nnot json\n[1,2]\n{{"kind":"mystery"}}\n\n'
        self.write_prior(prior)

        result = read_events(self.path)

        self.assertEqual(len(result.events), 1)
        self.assertEqual(result.malformed, (2, 3, 4))

        recorder = self.recorder("new")
        recorder.record("tool", {"name": "t"})
        text = self.path.read_text(encoding="utf-8")
        self.assertTrue(text.startswith(prior))
        self.assertEqual(read_events(self.path).events[-1]["seq"], 2)

    def test_a_run_cut_off_mid_line_keeps_its_fragment_on_its_own_line(self) -> None:
        self.write_prior('{"kind":"run","run_id":"old","seq":1,"timestamp":"t"}\n{"ki')

        self.recorder("new").record("tool", {"name": "t"})

        result = read_events(self.path)
        self.assertEqual(len(result.events), 2)
        self.assertEqual(result.malformed, (2,))

    def test_invalid_utf8_is_malformed_not_fatal(self) -> None:
        self.output.mkdir(parents=True)
        self.path.write_bytes(b'\xff\xfe{"kind":"run"}\n')

        result = read_events(self.path)

        self.assertEqual(result.events, ())
        self.assertEqual(result.malformed, (1,))


class FullRunTests(EvidenceTestCase):
    def test_a_full_fake_run_rereads_through_the_controller_parser(self) -> None:
        self.record_fake_run(self.recorder())

        result = read_events(self.path)

        self.assertEqual(result.malformed, ())
        self.assertEqual(
            [(e["kind"], e.get("name")) for e in result.events],
            [
                ("run", None),
                ("hook", "pre-construction"),
                ("tool", "openapi_schema_export"),
                ("hook", "post-generation"),
                ("acceptance", None),
            ],
        )


if __name__ == "__main__":
    unittest.main()
