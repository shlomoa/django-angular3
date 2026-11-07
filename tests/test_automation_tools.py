"""Credential-free conformance and failure-category tests of the Tool catalog.

External binaries (``oasdiff``, ``ng``, ``pnpm``) are replaced by a stand-in for
``command_execution.run_command``; nothing here needs a network, a provider or an
installed Angular CLI.
"""

import json
import re
import unittest
from pathlib import Path
from unittest.mock import patch

from django_angular3 import command_execution
from django_angular3.automation import tools as automation_tools
from django_angular3.automation.contracts import ContractError, FailureCategory
from django_angular3.automation.execution import (
    DirectExecutor,
    ExecutionContext,
    ToolCall,
)
from django_angular3.automation.tool_catalog import CATALOG, validate_inputs
from django_angular3.automation.tools import (
    invoke_tool,
    resolve_implementation,
    tool_function,
)
from django_angular3.tools import OasdiffUnavailableError
from tests.generate_automation_goldens import GOLDEN_DIR
from tests.test_step_execution import _Project
from tests.tool_config import use_tool_configuration_template

REPOSITORY = Path(__file__).resolve().parent.parent
CONTRACTS = REPOSITORY / "doc" / "contracts" / "TOOL_CONTRACTS.md"
RUN_COMMAND = "django_angular3.automation.tools.command_execution.run_command"
SCHEMA = {
    "openapi": "3.1.0",
    "info": {"title": "t", "version": "1"},
    "paths": {
        "/api/v1/customers/": {"get": {"responses": {"200": {"description": "ok"}}}}
    },
    "components": {"schemas": {"Customer": {"type": "object"}}},
}
# Recorded shape of ``oasdiff diff --format json`` output (a mock, not a binary run).
OASDIFF_JSON = {
    "paths": {
        "added": ["/api/v1/orders/"],
        "modified": {"/api/v1/customers/{id}/": {"operations": {}}},
    }
}


def setUpModule() -> None:
    use_tool_configuration_template()


def parse_contract() -> dict[str, dict[str, object]]:
    """Tool name -> input rows and output keys, read from the contract tables."""
    text = CONTRACTS.read_text(encoding="utf-8")
    parts = re.split(r"\n#### \d+\. `([a-z_]+)`", text)
    tools: dict[str, dict[str, object]] = {}

    def rows(block: str) -> list[list[str]]:
        return [
            [cell.strip() for cell in line.strip("|").split("|")]
            for line in block.splitlines()
            if line.startswith("|")
            and not line.startswith("|---")
            and not line.startswith("| Key")
        ]

    for index in range(1, len(parts), 2):
        body = parts[index + 1]
        inputs = re.search(r"\*\*Inputs\*\*:(.*?)\*\*Outputs\*\*", body, re.S)
        outputs = re.search(r"\*\*Outputs\*\*:(.*?)\*\*Error behavior", body, re.S)
        assert inputs and outputs, parts[index]
        tools[parts[index]] = {
            "inputs": {
                row[0].strip("`"): row[1] == "yes" for row in rows(inputs.group(1))
            },
            "outputs": [row[0].strip("`") for row in rows(outputs.group(1))],
        }
    return tools


class CatalogConformanceTests(unittest.TestCase):
    def test_the_catalog_names_the_tools_of_the_contract(self) -> None:
        self.assertEqual(sorted(CATALOG), sorted(parse_contract()))

    def test_every_tool_matches_its_contract_table(self) -> None:
        contract = parse_contract()
        for name, spec in CATALOG.items():
            with self.subTest(name):
                self.assertEqual(
                    {item.name: item.required for item in spec.inputs},
                    contract[name]["inputs"],
                )
                self.assertEqual(list(spec.outputs), contract[name]["outputs"])

    def test_every_implementation_reference_resolves(self) -> None:
        for name, spec in CATALOG.items():
            with self.subTest(name):
                self.assertTrue(callable(resolve_implementation(spec)))

    def test_the_catalog_matches_the_generated_golden(self) -> None:
        document = {
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
        golden = (GOLDEN_DIR / "tool-catalog.json").read_text(encoding="utf-8")
        self.assertEqual(json.dumps(document, indent=2) + "\n", golden)

    def test_tools_start_processes_only_through_command_execution(self) -> None:
        source = Path(automation_tools.__file__).read_text(encoding="utf-8")
        self.assertNotIn("import subprocess", source)
        self.assertNotIn("subprocess.", source)


class InputValidationTests(unittest.TestCase):
    def test_a_missing_required_input_is_invalid_input(self) -> None:
        for name, spec in CATALOG.items():
            required = [i.name for i in spec.inputs if i.required]
            if not required:
                continue
            with self.subTest(name), self.assertRaises(ContractError) as ctx:
                validate_inputs(spec, {})
            self.assertEqual(ctx.exception.category, FailureCategory.INVALID_INPUT)

    def test_an_unknown_input_is_invalid_input(self) -> None:
        for name, spec in CATALOG.items():
            with self.subTest(name), self.assertRaises(ContractError) as ctx:
                validate_inputs(spec, {**self.minimal(spec), "nope": 1})
            self.assertEqual(ctx.exception.category, FailureCategory.INVALID_INPUT)

    def minimal(self, spec) -> dict:
        return {i.name: "x" for i in spec.inputs if i.required}

    def test_wrongly_typed_inputs_are_invalid_input(self) -> None:
        cases = [
            ("openapi_schema_export", {"format": "xml"}),
            ("openapi_schema_export", {"dry_run": "yes"}),
            ("ngdj_run_schematic", {"schematic": "page", "options": []}),
            ("ngdj_add_complex_component", {"name": "n", "path": "p", "features": []}),
            ("ngdj_add_page", {"name": "n", "path": "p", "access": "secret"}),
            (
                "oasdiff_changelog",
                {"current_schema": "a", "previous_schema": "b", "format": "pdf"},
            ),
        ]
        for name, inputs in cases:
            with (
                self.subTest(name=name, inputs=inputs),
                self.assertRaises(ContractError),
            ):
                validate_inputs(CATALOG[name], inputs)

    def test_features_may_be_a_string_or_a_list(self) -> None:
        spec = CATALOG["ngdj_add_complex_component"]
        for features in ("search", ["search", "sort"]):
            validate_inputs(spec, {"name": "n", "path": "p", "features": features})

    def test_an_unknown_tool_is_invalid_input(self) -> None:
        with self.assertRaises(ContractError):
            tool_function("rm_rf")


class ToolTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.project = _Project(self)
        self.root = self.project.root
        self.context = ExecutionContext(
            self.project.project_config,
            self.root / "build",
            "run-1",
            settings=self.project.settings,
        )
        self.calls: list[list[str]] = []

    def invoke(self, name: str, inputs: dict, handler=None):
        def run(argv, cwd=None, check=True, **_):
            self.calls.append(list(argv))
            if handler is not None:
                return handler(list(argv), cwd)
            return command_execution.CommandResult(0, "", "")

        with patch(RUN_COMMAND, run):
            return invoke_tool(name, inputs, self.context)

    def write_schema(self, name: str, document: dict | None = None) -> Path:
        path = self.root / name
        path.write_text(json.dumps(document or SCHEMA), encoding="utf-8")
        return path


class SchemaToolTests(ToolTestCase):
    def test_validation_reports_failures_without_raising(self) -> None:
        good = self.write_schema("good.json")
        bad = self.write_schema("bad.json", {"openapi": "3.1.0"})

        valid = self.invoke("validate_openapi_schema", {"schema": str(good)})
        invalid = self.invoke("validate_openapi_schema", {"schema": str(bad)})

        self.assertTrue(valid.ok and valid.output["valid"])
        self.assertEqual(valid.output["openapi_version"], "3.1.0")
        self.assertEqual(valid.output["resource_count"], 1)
        self.assertTrue(invalid.ok)
        self.assertFalse(invalid.output["valid"])
        self.assertTrue(invalid.output["errors"])

    def test_validation_input_failures(self) -> None:
        missing = self.invoke(
            "validate_openapi_schema", {"schema": str(self.root / "no.json")}
        )
        ruleset = self.invoke(
            "validate_openapi_schema",
            {"schema": str(self.write_schema("s.json")), "ruleset": "custom.yml"},
        )
        garbage = self.root / "garbage.json"
        garbage.write_text("{not json", encoding="utf-8")
        unreadable = self.invoke("validate_openapi_schema", {"schema": str(garbage)})

        for result in (missing, ruleset, unreadable):
            self.assertEqual(result.failure.category, FailureCategory.INVALID_INPUT)

    def oasdiff(self, argv, cwd):
        if "diff" in argv:
            return command_execution.CommandResult(0, json.dumps(OASDIFF_JSON), "")
        return command_execution.CommandResult(0, "## Changes\n- added /orders\n", "")

    def pair(self) -> dict:
        return {
            "current_schema": str(self.write_schema("cur.json")),
            "previous_schema": str(self.write_schema("prev.json")),
        }

    def test_the_diff_is_structured_from_recorded_oasdiff_output(self) -> None:
        with patch("django_angular3.tools.ensure_oasdiff", return_value="oasdiff"):
            result = self.invoke(
                "oasdiff_diff",
                {**self.pair(), "report_path": str(self.root / "report.json")},
                self.oasdiff,
            )

        self.assertTrue(result.ok, result.failure)
        self.assertTrue(result.output["schema_changed"])
        self.assertEqual(
            list(result.output["affected_resources"]), ["customers", "orders"]
        )
        self.assertEqual([c["section"] for c in result.output["changes"]], ["paths"])
        self.assertEqual(
            json.loads((self.root / "report.json").read_text(encoding="utf-8")),
            OASDIFF_JSON,
        )

    def test_an_empty_diff_means_no_change(self) -> None:
        with patch("django_angular3.tools.ensure_oasdiff", return_value="oasdiff"):
            result = self.invoke(
                "oasdiff_diff",
                {**self.pair(), "report_path": str(self.root / "r.json")},
                lambda argv, cwd: command_execution.CommandResult(0, "", ""),
            )

        self.assertFalse(result.output["schema_changed"])
        self.assertEqual(list(result.output["changes"]), [])

    def test_oasdiff_failure_categories(self) -> None:
        pair = self.pair()
        cases = {
            "binary unavailable": (OasdiffUnavailableError("no oasdiff"), None),
            "exit code": (None, command_execution.CommandResult(2, "", "boom")),
            "not json": (None, command_execution.CommandResult(0, "<html>", "")),
            "not an object": (None, command_execution.CommandResult(0, "[1]", "")),
        }
        expected = {
            "binary unavailable": FailureCategory.MISSING_DEPENDENCY,
            "exit code": FailureCategory.EXTERNAL_TOOL_FAILED,
            "not json": FailureCategory.OUTPUT_INVALID,
            "not an object": FailureCategory.OUTPUT_INVALID,
        }
        for name, (error, outcome) in cases.items():
            with self.subTest(name):
                ensure = (
                    patch("django_angular3.tools.ensure_oasdiff", side_effect=error)
                    if error
                    else patch(
                        "django_angular3.tools.ensure_oasdiff", return_value="oasdiff"
                    )
                )
                with ensure:
                    result = self.invoke(
                        "oasdiff_diff", pair, lambda argv, cwd, o=outcome: o
                    )
                self.assertEqual(result.failure.category, expected[name])

    def test_a_missing_binary_is_a_missing_dependency(self) -> None:
        def missing(argv, cwd):
            raise command_execution.CommandExecutionError(
                f"Command not found: {argv[0]}"
            )

        with patch("django_angular3.tools.ensure_oasdiff", return_value="oasdiff"):
            result = self.invoke("oasdiff_diff", self.pair(), missing)

        self.assertEqual(result.failure.category, FailureCategory.MISSING_DEPENDENCY)

    def test_the_changelog_is_written_and_a_changed_schema_needs_content(self) -> None:
        out = self.root / "changelog.md"
        with patch("django_angular3.tools.ensure_oasdiff", return_value="oasdiff"):
            result = self.invoke(
                "oasdiff_changelog",
                {**self.pair(), "output_path": str(out)},
                self.oasdiff,
            )
            empty = self.invoke(
                "oasdiff_changelog",
                {**self.pair(), "output_path": str(self.root / "e.md")},
                lambda argv, cwd: command_execution.CommandResult(
                    0, json.dumps(OASDIFF_JSON) if "diff" in argv else "", ""
                ),
            )

        self.assertTrue(result.ok, result.failure)
        self.assertIn("added /orders", out.read_text(encoding="utf-8"))
        self.assertTrue(result.output["schema_changed"])
        self.assertEqual(empty.failure.category, FailureCategory.OUTPUT_INVALID)

    def test_the_changelog_dry_run_writes_nothing(self) -> None:
        out = self.root / "dry.md"

        result = self.invoke(
            "oasdiff_changelog",
            {**self.pair(), "output_path": str(out), "dry_run": True},
        )

        self.assertTrue(result.ok)
        self.assertFalse(out.exists())
        self.assertEqual(self.calls, [])


class ExportTests(ToolTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.destination = self.project.project_config.openapi_schema
        self.previous = self.destination.with_name("api.openapi.previous.json")
        self.destination.write_text(
            '{"openapi": "3.1.0", "old": true}', encoding="utf-8"
        )

    def export(self, writer, **inputs):
        def call_command(name, file, format, **_):
            writer(Path(file))

        with (
            patch("django.core.management.call_command", call_command),
            patch(
                "django_angular3.settings.load_drf_spectacular_settings",
                return_value={},
            ),
        ):
            return self.invoke("openapi_schema_export", inputs)

    def test_a_dry_run_modifies_nothing(self) -> None:
        before = self.destination.read_bytes()

        result = self.invoke("openapi_schema_export", {"dry_run": True})

        self.assertTrue(result.ok)
        self.assertEqual(self.destination.read_bytes(), before)
        self.assertFalse(self.previous.exists())
        self.assertEqual(result.output["previous_path"], str(self.previous))
        self.assertNotIn("bytes_written", result.output)

    def test_the_previous_schema_is_rotated(self) -> None:
        new = '{"openapi": "3.1.0", "new": true}'

        result = self.export(lambda path: path.write_text(new, encoding="utf-8"))

        self.assertTrue(result.ok, result.failure)
        self.assertEqual(self.destination.read_text(encoding="utf-8"), new)
        self.assertIn("old", self.previous.read_text(encoding="utf-8"))
        self.assertTrue(result.output["schema_changed"])
        self.assertEqual(result.output["bytes_written"], len(new))

    def test_an_identical_schema_is_not_a_change(self) -> None:
        same = self.destination.read_text(encoding="utf-8")

        result = self.export(lambda path: path.write_text(same, encoding="utf-8"))

        self.assertFalse(result.output["schema_changed"])

    def test_a_failure_restores_the_rotation(self) -> None:
        before = self.destination.read_bytes()

        def explode(path):
            raise RuntimeError("spectacular failed")

        result = self.export(explode)

        self.assertEqual(result.failure.category, FailureCategory.EXTERNAL_TOOL_FAILED)
        self.assertEqual(self.destination.read_bytes(), before)
        self.assertFalse(self.previous.exists())

    def test_an_invalid_schema_is_output_invalid_and_restores(self) -> None:
        before = self.destination.read_bytes()
        for content in ("", "{}", "not json"):
            with self.subTest(content=content):
                result = self.export(lambda path, c=content: path.write_text(c))
                self.assertEqual(
                    result.failure.category, FailureCategory.OUTPUT_INVALID
                )
                self.assertEqual(self.destination.read_bytes(), before)

    def test_a_missing_drf_spectacular_is_a_missing_dependency(self) -> None:
        with patch(
            "django_angular3.settings.load_drf_spectacular_settings",
            side_effect=ImportError("drf_spectacular"),
        ):
            result = self.invoke("openapi_schema_export", {})

        self.assertEqual(result.failure.category, FailureCategory.MISSING_DEPENDENCY)


class WrapperToolTests(ToolTestCase):
    def test_dry_runs_resolve_the_command_and_change_nothing(self) -> None:
        cases = {
            "angular_workspace_scaffold": {},
            "angular_app_scaffold": {},
            "angular_api_client_generate": {},
            "ngdj_add_component": {"name": "widget"},
            "ngdj_add_page": {"name": "home", "path": "src/app/features/home"},
            "ngdj_add_reactive_form": {
                "name": "contact",
                "definition": "contact.form.json",
            },
            "ngdj_add_complex_component": {
                "name": "board",
                "path": "src/app/features/board",
                "features": ["projection"],
            },
            "ngdj_add_data_service": {"resource": "customers"},
        }
        for name, inputs in cases.items():
            with self.subTest(name):
                result = self.invoke(name, {**inputs, "dry_run": True})
                self.assertTrue(result.ok, result.failure)
                self.assertTrue(result.output["command"])
                self.assertEqual(self.calls, [])
        self.assertFalse((self.project.workspace / "ng-openapi-gen.json").exists())

    def test_builder_validation_is_invalid_input(self) -> None:
        for name, inputs in (
            ("ngdj_add_page", {"name": "Bad Name", "path": "src/app/x"}),
            ("ngdj_add_page", {"name": "home", "path": "../outside"}),
            ("ngdj_add_component", {"name": "NotKebab"}),
        ):
            with self.subTest(name=name, inputs=inputs):
                result = self.invoke(name, inputs)
                self.assertEqual(result.failure.category, FailureCategory.INVALID_INPUT)
                self.assertEqual(self.calls, [])

    def test_the_generated_files_are_the_delta_of_the_run(self) -> None:
        workspace = self.project.workspace

        def generate(argv, cwd):
            target = workspace / "src/app/features/home"
            target.mkdir(parents=True, exist_ok=True)
            (target / "home.page.ts").write_text("x", encoding="utf-8")
            return command_execution.CommandResult(0, "", "")

        result = self.invoke(
            "ngdj_add_page",
            {"name": "home", "path": "src/app/features/home"},
            generate,
        )

        self.assertTrue(result.ok, result.failure)
        self.assertEqual(
            list(result.output["generated_files"]),
            ["src/app/features/home/home.page.ts"],
        )
        self.assertEqual(
            result.output["page_path"], str(workspace / "src/app/features/home")
        )

    def test_an_external_failure_is_structured(self) -> None:
        result = self.invoke(
            "ngdj_add_page",
            {"name": "home", "path": "src/app/features/home"},
            lambda argv, cwd: command_execution.CommandResult(3, "", "ng exploded"),
        )

        self.assertEqual(result.failure.category, FailureCategory.EXTERNAL_TOOL_FAILED)
        self.assertEqual(result.failure.details["returncode"], 3)
        self.assertIn("ng exploded", result.failure.details["stderr"])

    def test_a_component_without_source_is_output_invalid(self) -> None:
        result = self.invoke("ngdj_add_component", {"name": "widget"})

        self.assertEqual(result.failure.category, FailureCategory.OUTPUT_INVALID)

    def test_a_component_reports_class_and_selector(self) -> None:
        workspace = self.project.workspace

        def generate(argv, cwd):
            target = workspace / "src/app/widget"
            target.mkdir(parents=True, exist_ok=True)
            (target / "widget.ts").write_text(
                "@Component({ selector: 'app-widget' })\nexport class Widget {}\n",
                encoding="utf-8",
            )
            return command_execution.CommandResult(0, "", "")

        result = self.invoke("ngdj_add_component", {"name": "widget"}, generate)

        self.assertTrue(result.ok, result.failure)
        self.assertEqual(result.output["component_class"], "Widget")
        self.assertEqual(result.output["selector"], "app-widget")


class SchematicToolTests(ToolTestCase):
    def test_arbitrary_collections_and_unknown_schematics_are_rejected(self) -> None:
        for schematic in ("@evil/pkg:thing", "other:page", "../x", "no-such-schematic"):
            with self.subTest(schematic):
                result = self.invoke("ngdj_run_schematic", {"schematic": schematic})
                self.assertEqual(result.failure.category, FailureCategory.INVALID_INPUT)
        self.assertEqual(self.calls, [])

    def test_options_are_validated_and_translated(self) -> None:
        good = self.invoke(
            "ngdj_run_schematic",
            {
                "schematic": "angular-django2:page",
                "options": {"path": "src/app/features/home", "route_path": "home"},
                "dry_run": True,
            },
        )
        self.assertTrue(good.ok, good.failure)
        self.assertIn("angular-django2:page", good.output["command"])
        self.assertIn("--path=src/app/features/home", good.output["command"])
        self.assertIn("--route-path=home", good.output["command"])

        for options in ({"bogus": 1}, {"path": 3}, {"access": "secret"}):
            with self.subTest(options=options):
                result = self.invoke(
                    "ngdj_run_schematic",
                    {"schematic": "page", "options": options, "dry_run": True},
                )
                self.assertEqual(result.failure.category, FailureCategory.INVALID_INPUT)

    def test_a_run_reports_files_and_warnings(self) -> None:
        workspace = self.project.workspace

        def generate(argv, cwd):
            (workspace / "made.ts").write_text("x", encoding="utf-8")
            return command_execution.CommandResult(0, "ok\nWARN: skipped x\n", "")

        result = self.invoke(
            "ngdj_run_schematic",
            {"schematic": "page", "options": {"path": "src/app/features/home"}},
            generate,
        )

        self.assertTrue(result.ok, result.failure)
        self.assertEqual(list(result.output["generated_files"]), ["made.ts"])
        self.assertEqual(list(result.output["warnings"]), ["WARN: skipped x"])


class WidgetToolTests(ToolTestCase):
    def document(self) -> str:
        return str(self.project.document)

    def test_the_first_matching_element_is_compiled_by_default(self) -> None:
        result = self.invoke(
            "ngdj_add_tabs", {"document": self.document(), "dry_run": True}
        )
        # The test document has no tabs element: a failure names the document.
        self.assertEqual(result.failure.category, FailureCategory.INVALID_INPUT)

    def test_a_stepper_and_a_table_resolve_their_commands(self) -> None:
        document = self.project.workspace / "widgets.openui.json"
        document.write_text(
            json.dumps(
                {
                    "type": "html",
                    "id": "root",
                    "children": [
                        {"id": "setupWizard", "type": "Stepper"},
                        {"id": "orders", "type": "table"},
                    ],
                }
            ),
            encoding="utf-8",
        )
        for tool, schematic, node in (
            ("ngdj_add_stepper", "stepper", "setupWizard"),
            ("ngdj_add_table", "table", "orders"),
        ):
            with self.subTest(tool):
                result = self.invoke(tool, {"document": document.name, "dry_run": True})
                self.assertTrue(result.ok, result.failure)
                self.assertIn(f"angular-django2:{schematic}", result.output["command"])
                self.assertIn(f"--node-id={node}", result.output["command"])


class FeatureToolTests(ToolTestCase):
    ROUTES = (
        "import { Routes } from '@angular/router';\n\n"
        "export const routes: Routes = [\n"
        "  { path: 'home', component: Home }, // a ] in a comment\n"
        "  { path: 'x]y', component: Other },\n"
        "];\n"
    )

    def setUp(self) -> None:
        super().setUp()
        self.app = self.project.workspace / "src" / "app"
        self.app.mkdir(parents=True)
        self.routes = self.app / "app.routes.ts"
        self.routes.write_text(self.ROUTES, encoding="utf-8")

    def generate(self, argv, cwd):
        page = self.app / "features" / "reports" / "overview"
        page.mkdir(parents=True, exist_ok=True)
        (page / "overview.ts").write_text(
            "@Component({ selector: 'app-overview' })\nexport class Overview {}\n",
            encoding="utf-8",
        )
        return command_execution.CommandResult(0, "", "")

    def test_a_feature_is_created_and_registered(self) -> None:
        result = self.invoke(
            "ngdj_add_feature",
            {"name": "reports", "page_name": "overview"},
            self.generate,
        )

        self.assertTrue(result.ok, result.failure)
        feature = self.app / "features" / "reports"
        routes_file = feature / "reports.routes.ts"
        self.assertIn("m.Overview", routes_file.read_text(encoding="utf-8"))
        self.assertIn("REPORTS_ROUTES", routes_file.read_text(encoding="utf-8"))
        registered = self.routes.read_text(encoding="utf-8")
        self.assertIn("path: 'reports', loadChildren", registered)
        self.assertTrue(registered.rstrip().endswith("];"))
        self.assertIn("{ path: 'x]y', component: Other },", registered)
        self.assertEqual(
            result.output["page_component_path"],
            str(feature / "overview" / "overview.ts"),
        )
        self.assertEqual(result.output["app_routes_path"], str(self.routes))
        self.assertIn("reports.routes.ts", result.output["generated_files"])

    def test_registration_can_be_switched_off(self) -> None:
        result = self.invoke(
            "ngdj_add_feature",
            {"name": "reports", "page_name": "overview", "register_route": False},
            self.generate,
        )

        self.assertTrue(result.ok, result.failure)
        self.assertEqual(self.routes.read_text(encoding="utf-8"), self.ROUTES)
        self.assertIsNone(result.output["app_routes_path"])

    def test_invalid_features_are_invalid_input(self) -> None:
        (self.app / "features" / "taken").mkdir(parents=True)
        self.routes.rename(self.app / "moved.ts")
        cases = [
            {"name": "Reports"},
            {"name": "taken", "register_route": False},
            {"name": "reports"},  # no application route tree any more
            {"name": "reports", "path": "../outside", "register_route": False},
            {"name": "reports", "route_path": "bad path", "register_route": False},
        ]
        for inputs in cases:
            with self.subTest(inputs=inputs):
                result = self.invoke("ngdj_add_feature", inputs)
                self.assertEqual(result.failure.category, FailureCategory.INVALID_INPUT)
        self.assertEqual(self.calls, [])

    def test_a_dry_run_resolves_paths_and_writes_nothing(self) -> None:
        result = self.invoke("ngdj_add_feature", {"name": "reports", "dry_run": True})

        self.assertTrue(result.ok, result.failure)
        self.assertEqual(self.calls, [])
        self.assertFalse((self.app / "features").exists())
        self.assertEqual(self.routes.read_text(encoding="utf-8"), self.ROUTES)

    def test_generation_without_a_page_is_output_invalid(self) -> None:
        result = self.invoke("ngdj_add_feature", {"name": "reports"})

        self.assertEqual(result.failure.category, FailureCategory.OUTPUT_INVALID)


class ExecutorIntegrationTests(ToolTestCase):
    def test_a_tool_runs_under_the_direct_executor(self) -> None:
        good = self.write_schema("good.json")
        executor = DirectExecutor(self.context, [])

        result = executor.run(
            [
                ToolCall(
                    "validate_openapi_schema",
                    tool_function("validate_openapi_schema"),
                    {"schema": str(good)},
                )
            ]
        )

        self.assertTrue(result.ok, result.failure)
        self.assertTrue(result.steps[0].result.output["valid"])

    def test_invalid_input_stops_the_run_with_its_category(self) -> None:
        executor = DirectExecutor(self.context, [])

        result = executor.run(
            [ToolCall("oasdiff_diff", tool_function("oasdiff_diff"), {})]
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.failure.category, FailureCategory.INVALID_INPUT)


if __name__ == "__main__":
    unittest.main()
