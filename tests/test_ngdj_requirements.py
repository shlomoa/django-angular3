import json
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

from django_angular3.angular import resolve_angular_command
from tests.ngdj_source import NGDJ_PACKAGE_DIR, ngdj_required, require_ngdj_source

ROOT: Path = Path(__file__).resolve().parent.parent
PROJECT_CONFIG_PATH = ROOT / "tests" / "fixtures" / "django-angular3-project.json"


@require_ngdj_source
class NgdjRequirementsContractTests(unittest.TestCase):
    def _collection(self) -> Any:
        collection_path: Path = NGDJ_PACKAGE_DIR / "schematics" / "collection.json"
        self.assertTrue(collection_path.is_file())
        return json.loads(collection_path.read_text(encoding="utf-8"))

    def test_collection_exposes_required_schematics(self) -> None:
        schematics = self._collection().get("schematics", {})
        for name in (
            "ng-add",
            "application",
            "workspace-setup",
            "material-app",
            "material-setup",
            "openapi-setup",
            "data-service",
            "page",
            "component",
            "complex-component",
            "reactive-form",
        ):
            with self.subTest(schematic=name):
                self.assertIn(name, schematics)

    def test_ng_add_registers_angular_django2_in_schematic_collections(self) -> None:
        ng_add_index_path = NGDJ_PACKAGE_DIR / "schematics" / "ng-add" / "index.ts"
        self.assertTrue(ng_add_index_path.is_file())

        ng_add_source = ng_add_index_path.read_text(encoding="utf-8")
        self.assertIn("const COLLECTION_NAME = 'angular-django2';", ng_add_source)
        self.assertIn("schematicCollections", ng_add_source)
        self.assertIn("[COLLECTION_NAME, ...existingCollections]", ng_add_source)

    def test_application_schema_defaults_style_to_scss(self) -> None:
        schema_path = NGDJ_PACKAGE_DIR / "schematics" / "application" / "schema.json"
        self.assertTrue(schema_path.is_file())

        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        style_property = schema.get("properties", {}).get("style", {})
        self.assertEqual(style_property.get("default"), "scss")

    def test_material_app_schematic_creates_material_app(self) -> None:
        material_app_index_path = (
            NGDJ_PACKAGE_DIR / "schematics" / "material-app" / "index.ts"
        )
        self.assertTrue(material_app_index_path.is_file())

        source = material_app_index_path.read_text(encoding="utf-8")
        self.assertIn("externalSchematic('@schematics/angular', 'application'", source)
        self.assertIn("style: options.style", source)

    def test_openapi_setup_schematic_bootstraps_ng_openapi_gen(self) -> None:
        openapi_setup_index_path = (
            NGDJ_PACKAGE_DIR / "schematics" / "openapi-setup" / "index.ts"
        )
        self.assertTrue(openapi_setup_index_path.is_file())

        source = openapi_setup_index_path.read_text(encoding="utf-8")
        self.assertIn("ng-openapi-gen", source)
        self.assertIn("generate:api", source)

    def test_openapi_setup_schematic_offers_the_auth_scheme_djng_forwards(
        self,
    ) -> None:
        schema_path = NGDJ_PACKAGE_DIR / "schematics" / "openapi-setup" / "schema.json"
        properties = json.loads(schema_path.read_text(encoding="utf-8"))["properties"]
        self.assertEqual(set(properties["authScheme"]["enum"]), {"bearer", "basic"})
        self.assertIn("auth-scheme", properties["authScheme"]["aliases"])

    def test_schematics_accept_the_openui_document_options_djng_forwards(
        self,
    ) -> None:
        schematics = NGDJ_PACKAGE_DIR / "schematics"
        for name, has_node_id in (
            ("workspace-setup", False),
            ("material-app", True),
            ("page", True),
            ("component", True),
            ("complex-component", True),
            ("reactive-form", True),
        ):
            with self.subTest(schematic=name):
                properties = json.loads(
                    (schematics / name / "schema.json").read_text(encoding="utf-8")
                )["properties"]
                self.assertEqual(properties["document"]["format"], "path")
                self.assertEqual("nodeId" in properties, has_node_id)
                if has_node_id:
                    self.assertIn("node-id", properties["nodeId"]["aliases"])

    def _require_pinned_version(self) -> None:
        """Skip (fail when the ngdj source is required) unless the source is the pin."""
        pinned = json.loads(
            (ROOT / "tests" / "fixtures" / "ngdj" / "package.json").read_text(
                encoding="utf-8"
            )
        )["version"]
        source = json.loads(
            (NGDJ_PACKAGE_DIR / "package.json").read_text(encoding="utf-8")
        )["version"]
        if source != pinned:
            message = f"the ngdj source is {source}, tool.ngAddPackage pins {pinned}"
            if ngdj_required():
                self.fail(message)
            self.skipTest(message)

    def test_data_service_schematic_generates_typed_wrapper(self) -> None:
        self._require_pinned_version()
        ds_index_path = NGDJ_PACKAGE_DIR / "schematics" / "data-service" / "index.ts"
        self.assertTrue(ds_index_path.is_file())

        source = ds_index_path.read_text(encoding="utf-8")
        self.assertIn("DataService", source)
        self.assertIn("generateServiceContent(options, names, imports)", source)

    def test_data_service_schematic_resolves_the_generated_client(self) -> None:
        # 0.7.1: the import of the ng-openapi-gen client is computed from the
        # `output` of ng-openapi-gen.json (#240), not the fixed '../api/services'.
        self._require_pinned_version()
        api_client_path = (
            NGDJ_PACKAGE_DIR / "schematics" / "data-service" / "api-client.ts"
        )
        self.assertTrue(api_client_path.is_file())

        source = api_client_path.read_text(encoding="utf-8")
        self.assertIn("/ng-openapi-gen.json", source)
        self.assertIn("resolveApiClient", source)
        self.assertIn("verifyApiClient", source)

    def test_data_service_schematic_exposes_search_wrapper(self) -> None:
        ds_templates_path = (
            NGDJ_PACKAGE_DIR / "schematics" / "data-service" / "templates.ts"
        )
        self.assertTrue(ds_templates_path.is_file())

        source = ds_templates_path.read_text(encoding="utf-8")
        self.assertIn("search", source)

    def test_project_structure_declares_core_shared_features(self) -> None:
        directory_structure_path = (
            NGDJ_PACKAGE_DIR / "schematics" / "utility" / "directory-structure.ts"
        )
        self.assertTrue(directory_structure_path.is_file())

        source = directory_structure_path.read_text(encoding="utf-8")
        self.assertIn("'core'", source)
        self.assertIn("shared", source)
        self.assertIn("'features'", source)
        self.assertIn("project-structure", self._collection().get("schematics", {}))

    def test_openapi_setup_schematic_emits_django_integration_helpers(self) -> None:
        openapi_setup_templates_path = (
            NGDJ_PACKAGE_DIR / "schematics" / "openapi-setup" / "templates.ts"
        )
        self.assertTrue(openapi_setup_templates_path.is_file())

        source = openapi_setup_templates_path.read_text(encoding="utf-8")
        self.assertIn("django-transport.ts", source)
        self.assertIn("resource-adapter.ts", source)
        self.assertIn("provideDjangoApiTransport", source)


class DjngNgdjIntegrationContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.project_config_discovery = patch(
            "django_angular3.config.discover_project_config_path",
            return_value=PROJECT_CONFIG_PATH,
        )
        self.project_config_discovery.start()
        self.addCleanup(self.project_config_discovery.stop)

    def test_ng_workspace_uses_angular_django2_workspace_setup_schematic(self) -> None:
        invocations = resolve_angular_command("ng_workspace")
        self.assertEqual(len(invocations), 6)

        argv = invocations[-1].argv
        from django_angular3.settings import load_angular_settings

        self.assertEqual(argv[0], load_angular_settings().ng_executable)
        self.assertEqual(argv[1], "generate")
        self.assertEqual(argv[2], "angular-django2:workspace-setup")

    def test_ng_gen_app_uses_angular_django2_material_app_schematic(self) -> None:
        invocations = resolve_angular_command("ng_gen_app")
        self.assertEqual(len(invocations), 1)

        argv = invocations[0].argv
        from django_angular3.settings import load_angular_settings

        self.assertEqual(argv[0], load_angular_settings().ng_executable)
        self.assertEqual(argv[1], "generate")
        self.assertEqual(argv[2], "angular-django2:material-app")

    def test_ng_openapi_setup_uses_openapi_setup_schematic(self) -> None:
        invocations = resolve_angular_command("ng_openapi_setup")
        self.assertEqual(len(invocations), 1)

        argv = invocations[0].argv
        from django_angular3.settings import load_angular_settings

        self.assertEqual(argv[0], load_angular_settings().ng_executable)
        self.assertEqual(argv[1], "generate")
        self.assertEqual(argv[2], "angular-django2:openapi-setup")

    def test_ng_data_service_uses_data_service_schematic(self) -> None:
        invocations = resolve_angular_command("ng_data_service", resource="orders")
        self.assertEqual(len(invocations), 1)

        argv = invocations[0].argv
        from django_angular3.settings import load_angular_settings

        self.assertEqual(argv[0], load_angular_settings().ng_executable)
        self.assertEqual(argv[1], "generate")
        self.assertEqual(argv[2], "angular-django2:data-service")
        self.assertEqual(argv[3], "orders")

    def test_ng_material_setup_uses_material_setup_schematic(self) -> None:
        invocations = resolve_angular_command("ng_material_setup")
        self.assertEqual(len(invocations), 1)

        argv = invocations[0].argv
        from django_angular3.settings import load_angular_settings

        self.assertEqual(argv[0], load_angular_settings().ng_executable)
        self.assertEqual(argv[1], "generate")
        self.assertEqual(argv[2], "angular-django2:material-setup")

    def test_new_ui_wrappers_use_matching_ngdj_schematics(self) -> None:
        cases: dict[str, tuple[dict[str, object], str]] = {
            "ng_page": (
                {"name": "orders", "target_path": "src/app/features/orders"},
                "page",
            ),
            "ng_component": ({"name": "order-card"}, "component"),
            "ng_reactive_form": (
                {"name": "contact", "definition": "forms/contact.json"},
                "reactive-form",
            ),
        }

        for wrapper, (options, schematic) in cases.items():
            with self.subTest(wrapper=wrapper):
                invocation = resolve_angular_command(wrapper, **options)[0]
                self.assertEqual(invocation.command_name, wrapper)
                self.assertEqual(invocation.argv[1], "generate")
                self.assertEqual(invocation.argv[2], f"angular-django2:{schematic}")


if __name__ == "__main__":
    unittest.main()
