import json
import unittest
from pathlib import Path
from typing import Any

from django_angular3.angular import resolve_angular_command

ROOT: Path = Path(__file__).resolve().parent.parent
NGDJ_ROOT: Path = ROOT.parent / "angular-django2"


@unittest.skipUnless(
    NGDJ_ROOT.is_dir(), "angular-django2 sibling repository is required"
)
class NgdjRequirementsContractTests(unittest.TestCase):
    def _collection(self) -> Any:
        collection_path: Path = (
            NGDJ_ROOT
            / "projects"
            / "angular-django2"
            / "schematics"
            / "collection.json"
        )
        self.assertTrue(collection_path.is_file())
        return json.loads(collection_path.read_text(encoding="utf-8"))

    def test_collection_exposes_required_schematics(self) -> None:
        schematics = self._collection().get("schematics", {})
        for name in (
            "ng-add",
            "application",
            "workspace-setup",
            "material-app",
            "openapi-setup",
            "data-service",
        ):
            with self.subTest(schematic=name):
                self.assertIn(name, schematics)

    def test_ng_add_registers_angular_django2_in_schematic_collections(self) -> None:
        ng_add_index_path = (
            NGDJ_ROOT
            / "projects"
            / "angular-django2"
            / "schematics"
            / "ng-add"
            / "index.ts"
        )
        self.assertTrue(ng_add_index_path.is_file())

        ng_add_source = ng_add_index_path.read_text(encoding="utf-8")
        self.assertIn("const COLLECTION_NAME = 'angular-django2';", ng_add_source)
        self.assertIn("schematicCollections", ng_add_source)
        self.assertIn("[COLLECTION_NAME, ...existingCollections]", ng_add_source)

    def test_application_schema_defaults_style_to_scss(self) -> None:
        schema_path = (
            NGDJ_ROOT
            / "projects"
            / "angular-django2"
            / "schematics"
            / "application"
            / "schema.json"
        )
        self.assertTrue(schema_path.is_file())

        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        style_property = schema.get("properties", {}).get("style", {})
        self.assertEqual(style_property.get("default"), "scss")

    def test_material_app_schematic_creates_material_app(self) -> None:
        material_app_index_path = (
            NGDJ_ROOT
            / "projects"
            / "angular-django2"
            / "schematics"
            / "material-app"
            / "index.ts"
        )
        self.assertTrue(material_app_index_path.is_file())

        source = material_app_index_path.read_text(encoding="utf-8")
        self.assertIn("externalSchematic('@schematics/angular', 'application'", source)
        self.assertIn("style: options.style", source)

    def test_openapi_setup_schematic_bootstraps_ng_openapi_gen(self) -> None:
        openapi_setup_index_path = (
            NGDJ_ROOT
            / "projects"
            / "angular-django2"
            / "schematics"
            / "openapi-setup"
            / "index.ts"
        )
        self.assertTrue(openapi_setup_index_path.is_file())

        source = openapi_setup_index_path.read_text(encoding="utf-8")
        self.assertIn("ng-openapi-gen", source)
        self.assertIn("generate:api", source)

    def test_data_service_schematic_generates_typed_wrapper(self) -> None:
        ds_index_path = (
            NGDJ_ROOT
            / "projects"
            / "angular-django2"
            / "schematics"
            / "data-service"
            / "index.ts"
        )
        self.assertTrue(ds_index_path.is_file())

        source = ds_index_path.read_text(encoding="utf-8")
        self.assertIn("DataService", source)
        self.assertIn("generateServiceContent(options, names)", source)


class DjngNgdjIntegrationContractTests(unittest.TestCase):
    def test_ng_workspace_uses_angular_django2_workspace_setup_schematic(self) -> None:
        invocations = resolve_angular_command(
            "ng_workspace", ROOT / "django-angular3.json"
        )
        self.assertEqual(len(invocations), 6)

        argv = invocations[-1].argv
        from django_angular3.settings import DEFAULT_ANGULAR_SETTINGS

        self.assertEqual(argv[0], DEFAULT_ANGULAR_SETTINGS["ng_executable"])
        self.assertEqual(argv[1], "generate")
        self.assertEqual(argv[2], "angular-django2:workspace-setup")

    def test_ng_gen_app_uses_angular_django2_material_app_schematic(self) -> None:
        invocations = resolve_angular_command(
            "ng_gen_app", ROOT / "django-angular3.json"
        )
        self.assertEqual(len(invocations), 1)

        argv = invocations[0].argv
        from django_angular3.settings import DEFAULT_ANGULAR_SETTINGS

        self.assertEqual(argv[0], DEFAULT_ANGULAR_SETTINGS["ng_executable"])
        self.assertEqual(argv[1], "generate")
        self.assertEqual(argv[2], "angular-django2:material-app")


if __name__ == "__main__":
    unittest.main()
