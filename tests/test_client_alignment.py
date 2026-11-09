"""The terminal check that the generated client matches the OpenAPI contract."""

import json
import unittest

from django_angular3.client_alignment import (
    CLIENT_ALIGNMENT_COMMAND,
    check_client_alignment,
    with_client_alignment_step,
)
from django_angular3.step_execution import (
    STATUS_FAILED,
    STATUS_SUCCEEDED,
    StepRecord,
    _run_client_alignment,
)
from tests.test_step_execution import _Project
from tests.tool_config import use_tool_configuration_template

SCHEMA = {
    "openapi": "3.1.0",
    "info": {"title": "t", "version": "1"},
    "paths": {
        "/api/v1/customers/": {
            "get": {
                "operationId": "customers_list",
                "responses": {"200": {"description": "ok"}},
            }
        }
    },
    "components": {"schemas": {"Customer": {"type": "object"}}},
}


def setUpModule() -> None:
    use_tool_configuration_template()


class AlignmentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.project = _Project(self)
        self.config = self.project.project_config
        self.config.openapi_schema.write_text(json.dumps(SCHEMA), encoding="utf-8")
        self.workspace = self.config.angular_workspace
        self.output = self.workspace / "src" / "api"

    def generate(self, model: str, service: str) -> None:
        (self.workspace / "ng-openapi-gen.json").write_text(
            json.dumps({"output": "src/api"}), encoding="utf-8"
        )
        (self.output / "models").mkdir(parents=True, exist_ok=True)
        (self.output / "services").mkdir(parents=True, exist_ok=True)
        (self.output / "models" / "customer.ts").write_text(model, encoding="utf-8")
        (self.output / "services" / "customers-api.service.ts").write_text(
            service, encoding="utf-8"
        )

    def test_a_client_that_declares_every_schema_and_operation_is_aligned(self) -> None:
        self.generate(
            "export interface Customer { name: string }\n",
            "export class CustomersApiService { customersList$Response() {} }\n",
        )

        errors, summary = check_client_alignment(self.config)

        self.assertEqual(errors, [])
        self.assertEqual(summary, "1 schema(s) and 1 operation(s) checked")

    def test_a_schema_without_a_model_is_reported(self) -> None:
        self.generate(
            "export interface Product { name: string }\n",
            "export class CustomersApiService { customersList() {} }\n",
        )

        errors, _ = check_client_alignment(self.config)

        self.assertEqual(errors, ["schema Customer has no generated model"])

    def test_an_operation_without_a_service_method_is_reported(self) -> None:
        self.generate(
            "export interface Customer { name: string }\n",
            "export class CustomersApiService { customersRetrieve() {} }\n",
        )

        errors, _ = check_client_alignment(self.config)

        self.assertEqual(
            errors, ["operation customers_list has no generated service method"]
        )

    def test_a_project_without_a_generated_client_has_nothing_to_align(self) -> None:
        errors, summary = check_client_alignment(self.config)

        self.assertEqual(errors, [])
        self.assertIn("no generated client", summary)

    def test_the_step_sits_before_the_gate_and_only_when_there_are_steps(self) -> None:
        self.assertEqual(with_client_alignment_step(()), ())

    def test_interface_drift_fails_the_step_and_names_the_mismatch(self) -> None:
        # The contract gained an operation after the client was generated.
        self.generate(
            "export interface Customer { name: string }\n",
            "export class CustomersApiService { customersList() {} }\n",
        )
        drifted = json.loads(json.dumps(SCHEMA))
        drifted["paths"]["/api/v1/orders/"] = {
            "get": {
                "operationId": "orders_list",
                "responses": {"200": {"description": "ok"}},
            }
        }
        self.config.openapi_schema.write_text(json.dumps(drifted), encoding="utf-8")
        (step,) = with_client_alignment_step((_gate_step(),))[:1]
        record = StepRecord(step)

        passed = _run_client_alignment(record, self.config)

        self.assertFalse(passed)
        self.assertEqual(record.status, STATUS_FAILED)
        self.assertIn("orders_list", record.error)
        self.assertEqual(step.command, CLIENT_ALIGNMENT_COMMAND)

    def test_an_aligned_client_passes_the_step(self) -> None:
        self.generate(
            "export interface Customer { name: string }\n",
            "export class CustomersApiService { customersList() {} }\n",
        )
        (step,) = with_client_alignment_step((_gate_step(),))[:1]
        record = StepRecord(step)

        self.assertTrue(_run_client_alignment(record, self.config))
        self.assertEqual(record.status, STATUS_SUCCEEDED)


def _gate_step():
    from django_angular3.command_translation import AppBuildStep

    return AppBuildStep(
        name_id="last-check",
        exec_order=12,
        change_op="validate",
        change_reason="Validate the outputs of all the steps.",
        change_target="changeset",
        change_domain=None,
    )


if __name__ == "__main__":
    unittest.main()
