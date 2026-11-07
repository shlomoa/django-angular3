"""The failure output of the end-to-end flow names the failing Playwright test."""

import json
import tempfile
import unittest
from pathlib import Path

from tests.e2e.run_e2e import failure_output, playwright_failures
from tests.workspace_temp import WORKSPACE_TEMP_DIR

MESSAGE = "expect(received).toBe(expected)\nExpected: 201\nReceived: 403"

REPORT = {
    "suites": [
        {
            "title": "django-writes.spec.ts",
            "specs": [],
            "suites": [
                {
                    "title": "sign-in and CSRF-protected writes",
                    "specs": [
                        {
                            "title": "W2 a signed-in write succeeds",
                            "tests": [
                                {
                                    "results": [
                                        {
                                            "status": "failed",
                                            "error": {"message": MESSAGE},
                                        }
                                    ]
                                }
                            ],
                        },
                        {
                            "title": "W1 sign-in",
                            "tests": [{"results": [{"status": "passed"}]}],
                        },
                    ],
                }
            ],
        }
    ]
}


class PlaywrightFailureTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(dir=WORKSPACE_TEMP_DIR)
        self.addCleanup(temporary.cleanup)
        self.results = Path(temporary.name) / "results.json"

    def test_the_failing_test_and_its_assertion_are_named(self) -> None:
        self.results.write_text(json.dumps(REPORT), encoding="utf-8")

        failures = playwright_failures(self.results)

        self.assertEqual(len(failures), 1)
        self.assertIn("django-writes.spec.ts", failures[0])
        self.assertIn("W2 a signed-in write succeeds", failures[0])
        self.assertIn("Expected: 201 Received: 403", failures[0])
        self.assertNotIn("W1 sign-in", failures[0])

    def test_a_missing_or_malformed_report_gives_no_failures(self) -> None:
        self.assertEqual(playwright_failures(self.results), [])
        self.results.write_text("not json", encoding="utf-8")
        self.assertEqual(playwright_failures(self.results), [])

    def test_a_timeout_is_reported_too(self) -> None:
        report = json.loads(json.dumps(REPORT))
        result = report["suites"][0]["suites"][0]["specs"][0]["tests"][0]["results"][0]
        result["status"] = "timedOut"
        result["error"] = {"message": "Test timeout of 60000ms exceeded."}
        self.results.write_text(json.dumps(report), encoding="utf-8")

        (failure,) = playwright_failures(self.results)

        self.assertIn("Test timeout of 60000ms exceeded.", failure)


class FailureOutputTests(unittest.TestCase):
    def test_neither_stream_hides_the_other(self) -> None:
        text = failure_output("1) W2 failed", "GET /api/v1/customers/ 200")

        self.assertIn("--- stdout (tail) ---\n1) W2 failed", text)
        self.assertIn("--- stderr (tail) ---\nGET /api/v1/customers/ 200", text)

    def test_only_the_tail_of_a_long_stream_is_kept(self) -> None:
        text = failure_output("x" * 10000 + "END", "")

        self.assertTrue(text.endswith("END"))
        self.assertLess(len(text), 4200)

    def test_no_output_is_said_so(self) -> None:
        self.assertEqual(failure_output(" ", ""), "(no output)")


if __name__ == "__main__":
    unittest.main()
