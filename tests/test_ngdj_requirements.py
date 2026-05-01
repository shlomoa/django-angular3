import json
import unittest
from pathlib import Path

from django_angular3.angular import plan_angular_command


ROOT = Path(__file__).resolve().parent.parent
NGDJ_ROOT = ROOT.parent / "angular-django2"


@unittest.skipUnless(NGDJ_ROOT.is_dir(), "angular-django2 sibling repository is required")
class NgdjRequirementsContractTests(unittest.TestCase):
    def test_collection_exposes_ng_add_and_application_schematics(self) -> None:
        collection_path = (
            NGDJ_ROOT / "projects" / "angular-django2" / "schematics" / "collection.json"
        )
        self.assertTrue(collection_path.is_file())

        collection = json.loads(collection_path.read_text(encoding="utf-8"))
        schematics = collection.get("schematics", {})

        self.assertIn("ng-add", schematics)
        self.assertIn("application", schematics)

    def test_ng_add_registers_angular_django2_in_schematic_collections(self) -> None:
        ng_add_index_path = (
            NGDJ_ROOT / "projects" / "angular-django2" / "schematics" / "ng-add" / "index.ts"
        )
        self.assertTrue(ng_add_index_path.is_file())

        ng_add_source = ng_add_index_path.read_text(encoding="utf-8")
        self.assertIn("const COLLECTION_NAME = 'angular-django2';", ng_add_source)
        self.assertIn("schematicCollections", ng_add_source)
        self.assertIn("[COLLECTION_NAME, ...existingCollections]", ng_add_source)

    def test_application_schema_defaults_style_to_scss(self) -> None:
        schema_path = (
            NGDJ_ROOT / "projects" / "angular-django2" / "schematics" / "application" / "schema.json"
        )
        self.assertTrue(schema_path.is_file())

        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        style_property = schema.get("properties", {}).get("style", {})
        self.assertEqual(style_property.get("default"), "scss")

    def test_application_implementation_applies_scss_default(self) -> None:
        application_index_path = (
            NGDJ_ROOT
            / "projects"
            / "angular-django2"
            / "schematics"
            / "application"
            / "index.ts"
        )
        self.assertTrue(application_index_path.is_file())

        application_source = application_index_path.read_text(encoding="utf-8")
        self.assertIn("externalSchematic('@schematics/angular', 'application'", application_source)
        self.assertIn("style: 'scss'", application_source)


class DjngNgdjIntegrationContractTests(unittest.TestCase):
    def test_ng_gen_app_uses_angular_django2_application_schematic(self) -> None:
        invocations = plan_angular_command("ng_gen_app", ROOT / "django-angular3.json")
        self.assertEqual(len(invocations), 1)

        argv = invocations[0].argv
        self.assertEqual(argv[0], "ng")
        self.assertEqual(argv[1], "generate")
        self.assertEqual(argv[2], "angular-django2:application")


if __name__ == "__main__":
    unittest.main()
