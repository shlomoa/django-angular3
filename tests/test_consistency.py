import json
import unittest
from pathlib import Path

from django_angular3.config import load_project_config
from django_angular3.consistency import (
    extract_references,
    method_name,
    reference_index,
)
from django_angular3.validation import validate_consistency, validate_project_config

SCENARIOS = Path(__file__).resolve().parent / "fixtures" / "scenarios"
SHARED = SCENARIOS / "shared"
SCENARIO = SCENARIOS / "13-dangling-binding"


def _load(name: str):
    return json.loads((SHARED / name).read_text(encoding="utf-8"))


class ReferenceIndexTests(unittest.TestCase):
    def test_method_names_follow_the_generator(self) -> None:
        self.assertEqual(method_name("auth_register"), "authRegister")
        self.assertEqual(method_name("listUsers"), "listUsers")
        self.assertEqual(method_name("v1_customers_list"), "v1CustomersList")

    def test_a_valid_document_resolves_every_reference_to_operations(self) -> None:
        index = reference_index(
            _load("bindings.openui.json"), _load("bindings.openapi.json")
        )

        self.assertEqual(index.errors, ())
        self.assertEqual(
            [(r.node_id, r.attribute) for r in index.references],
            [("root", "behaves.submit"), ("usersGrid", "uses.data")],
        )
        self.assertEqual(
            [(o.http_method, o.path) for o in index.operations_of("root")],
            [("post", "/api/users/")],
        )
        self.assertEqual(
            sorted(o.method for o in index.operations_of("usersGrid")),
            ["createUser", "listUsers"],
        )

    def test_a_dangling_document_names_the_node_and_what_is_missing(self) -> None:
        index = reference_index(
            _load("dangling.openui.json"), _load("bindings.openapi.json")
        )

        self.assertEqual(len(index.errors), 2)
        self.assertIn("node 'root', behaves.submit", index.errors[0])
        self.assertIn("UsersApiService.deleteUser", index.errors[0])
        self.assertIn("node 'usersGrid', uses.data", index.errors[1])
        self.assertIn("OrdersApiService", index.errors[1])

    def test_values_without_an_artifact_are_not_references(self) -> None:
        document = {
            "id": "root",
            "type": "Form",
            "attrs": {"behaves.submit": "onSubmit(form.value)", "uses.data": "orders"},
        }
        self.assertEqual(extract_references(document), ())


class ScenarioTests(unittest.TestCase):
    def test_the_dangling_binding_scenario_fails_project_validation(self) -> None:
        config = load_project_config(
            SCENARIO / "django-angular3-scenario-dangling-binding.json"
        )

        errors = validate_project_config(config)

        self.assertEqual(errors, validate_consistency(config))
        self.assertEqual(len(errors), 2)
        self.assertIn("usersGrid", " ".join(errors))


if __name__ == "__main__":
    unittest.main()
