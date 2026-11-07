"""Credential-free tests of the provider-neutral automation contracts."""

import copy
import dataclasses
import json
import subprocess
import sys
import unittest
from pathlib import Path

from django_angular3.automation import contracts
from django_angular3.automation.contracts import (
    REDACTED,
    AdapterResult,
    AdapterStatus,
    AutomationFailure,
    Consequence,
    ContractError,
    FailureCategory,
    HookFamily,
    HookOutcome,
    ToolResult,
    apply_evidence_policy,
    freeze_request,
)
from tests.automation_samples import FAILURE, SAMPLES
from tests.generate_automation_goldens import GOLDEN_DIR

ROOT = Path(__file__).resolve().parent.parent
PROVIDER_MODULES = ("claude_agent_sdk", "openai", "google.genai", "copilot")


class ImmutabilityTests(unittest.TestCase):
    def test_models_reject_attribute_assignment(self):
        for name, sample in SAMPLES.items():
            with self.subTest(name), self.assertRaises(dataclasses.FrozenInstanceError):
                sample.tool = "x" if hasattr(sample, "tool") else None
                sample.status = None

    def test_nested_values_are_read_only(self):
        with self.assertRaises(TypeError):
            SAMPLES["tool-result-ok"].output["format"] = "yaml"
        with self.assertRaises(TypeError):
            SAMPLES["adapter-result"].evidence["session"] = "other"


class SerializationTests(unittest.TestCase):
    def test_golden_files_match_byte_for_byte(self):
        for name, sample in SAMPLES.items():
            with self.subTest(name):
                golden = (GOLDEN_DIR / f"{name}.json").read_bytes()
                self.assertEqual(sample.to_json().encode("utf-8") + b"\n", golden)

    def test_round_trip(self):
        for name, cls in (
            ("failure", AutomationFailure),
            ("tool-result-ok", ToolResult),
            ("tool-result-failed", ToolResult),
            ("hook-outcome-halt", HookOutcome),
            ("adapter-result", AdapterResult),
        ):
            with self.subTest(name):
                sample = SAMPLES[name]
                self.assertEqual(cls.from_dict(json.loads(sample.to_json())), sample)

    def test_identical_inputs_serialize_identically_regardless_of_key_order(self):
        a = ToolResult("t", {"a": 1, "b": [1, 2], "c": {"x": 1, "y": 2}})
        b = ToolResult("t", {"c": {"y": 2, "x": 1}, "b": [1, 2], "a": 1})
        self.assertEqual(a.to_json(), b.to_json())

    def test_non_ascii_is_kept_as_utf8(self):
        text = ToolResult("t", {"label": "גינה"}).to_json()
        self.assertIn("גינה", text)


class ValidationTests(unittest.TestCase):
    def assertInvalid(self, call, category=FailureCategory.INVALID_INPUT):
        with self.assertRaises(ContractError) as ctx:
            call()
        self.assertEqual(ctx.exception.category, category)
        self.assertEqual(ctx.exception.to_failure().category, category)

    def test_missing_field(self):
        self.assertInvalid(lambda: AutomationFailure.from_dict({"category": "timeout"}))

    def test_wrong_type(self):
        self.assertInvalid(
            lambda: AutomationFailure.from_dict(
                {"category": "timeout", "message": 3, "details": {}}
            )
        )

    def test_boolean_is_not_a_string(self):
        self.assertInvalid(
            lambda: ToolResult.from_dict({"tool": True, "output": {}, "failure": None})
        )

    def test_unknown_category(self):
        self.assertInvalid(
            lambda: AutomationFailure.from_dict(
                {"category": "nope", "message": "m", "details": {}}
            )
        )

    def test_unknown_field(self):
        self.assertInvalid(
            lambda: AdapterResult.from_dict(
                {"status": "accepted", "evidence": {}, "extra": 1}
            )
        )

    def test_non_json_value(self):
        self.assertInvalid(lambda: ToolResult("t", {"x": object()}))
        self.assertInvalid(lambda: ToolResult("t", {"x": float("nan")}))
        self.assertInvalid(lambda: ToolResult("t", {1: "x"}))

    def test_failed_result_carries_no_output(self):
        self.assertInvalid(lambda: ToolResult("t", {"x": 1}, FAILURE))

    def test_empty_names_rejected(self):
        self.assertInvalid(lambda: ToolResult("", {}))
        self.assertInvalid(lambda: HookOutcome("", HookFamily.PRE_TOOL))
        self.assertInvalid(lambda: AutomationFailure(FailureCategory.TIMEOUT, "", {}))


class ConsequenceTests(unittest.TestCase):
    def test_consequence_follows_the_lifecycle_family(self):
        expected = {
            HookFamily.PRE_TOOL: Consequence.BLOCK,
            HookFamily.POST_TOOL: Consequence.HALT,
            HookFamily.SESSION_STOP: Consequence.WARN,
        }
        for family, consequence in expected.items():
            with self.subTest(family):
                self.assertEqual(
                    HookOutcome("h", family, FAILURE).consequence, consequence
                )
                self.assertIsNone(HookOutcome("h", family).consequence)


class EvidencePolicyTests(unittest.TestCase):
    def test_sensitive_fields_are_redacted(self):
        record = {
            "event": "tool",
            "Authorization": "Bearer abc.def",
            "cookie": "sid=1",
            "api_key": "k",
            "db_password": "p",
            "headers": {"X-Other": "v"},
            "nested": [{"token": "t", "ok": 1}],
            "output": "sent Bearer abc123 and Basic dXNlcjpwdw== today",
        }
        result = apply_evidence_policy(record)
        text = json.dumps(result)
        for canary in ("abc.def", "sid=1", "dXNlcjpwdw==", "abc123", "X-Other"):
            self.assertNotIn(canary, text)
        self.assertEqual(result["Authorization"], REDACTED)
        self.assertEqual(result["headers"], REDACTED)
        self.assertEqual(result["nested"][0], {"token": REDACTED, "ok": 1})
        self.assertEqual(result["event"], "tool")

    def test_provider_native_payload_is_rejected(self):
        for key in ("provider_payload", "raw_response", "native"):
            with self.subTest(key), self.assertRaises(ContractError) as ctx:
                apply_evidence_policy({"outer": {key: {"x": 1}}})
            self.assertEqual(ctx.exception.category, FailureCategory.EVIDENCE_REJECTED)

    def test_policy_does_not_mutate_its_input(self):
        record = {"token": "t", "list": [{"password": "p"}]}
        before = copy.deepcopy(record)
        apply_evidence_policy(record)
        self.assertEqual(record, before)

    def test_policy_is_deterministic(self):
        record = {"b": "Bearer x", "a": {"secret": "s"}}
        self.assertEqual(
            contracts.dumps(apply_evidence_policy(record)),
            contracts.dumps(apply_evidence_policy(copy.deepcopy(record))),
        )


class AdapterProtocolTests(unittest.TestCase):
    def test_adapter_cannot_mutate_the_request(self):
        request = {"skill": "s", "options": {"a": [1, 2]}}
        before = copy.deepcopy(request)
        frozen = freeze_request(request)
        with self.assertRaises(TypeError):
            frozen["skill"] = "other"
        with self.assertRaises(TypeError):
            frozen["options"]["a"] = ()
        self.assertEqual(request, before)

    def test_stub_adapter_satisfies_the_protocol(self):
        class Stub:
            def run(self, request):
                return AdapterResult(AdapterStatus.UNMET_ACCEPTANCE, {})

        result = Stub().run(freeze_request({"skill": "s"}))
        self.assertFalse(result.accepted)


class ImportHygieneTests(unittest.TestCase):
    def test_package_imports_no_provider_sdk(self):
        code = (
            "import sys, django_angular3.automation.contracts\n"
            f"bad = [m for m in {PROVIDER_MODULES!r} if m in sys.modules]\n"
            "sys.exit(1 if bad else 0)"
        )
        completed = subprocess.run(
            [sys.executable, "-I", "-c", code], cwd=ROOT, check=False
        )
        self.assertEqual(completed.returncode, 0)

    def test_production_modules_have_no_provider_imports(self):
        for path in (ROOT / "django_angular3" / "automation").rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            for module in PROVIDER_MODULES:
                with self.subTest(path.name, module=module):
                    self.assertNotIn(f"import {module}", text)
                    self.assertNotIn(f"from {module}", text)


if __name__ == "__main__":
    unittest.main()
