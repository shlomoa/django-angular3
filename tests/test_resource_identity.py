import json
import unittest
from pathlib import Path

from django_angular3.documents import load_document
from django_angular3.resource_identity import (
    ResourceIdentityError,
    SubjectNotInDocument,
    binding_service,
    resource_identity,
    service_class_name,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "service-names"


def _generated(name: str) -> set[str]:
    document = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    return set(document["classes"])


class GeneratedServiceNameTests(unittest.TestCase):
    """The rule against the real ng-openapi-gen output (generate_service_names)."""

    def test_every_tag_shape_names_the_class_the_generator_emitted(self) -> None:
        document = load_document(FIXTURES / "tags.openapi.json")
        generated = _generated("tags.services.json")
        tagged = {
            operation["tags"][0]
            for item in document["paths"].values()
            for operation in item.values()
            if "tags" in operation
        }

        outside = {tag for tag in tagged if tag == "my tag_x"}
        for tag in outside:
            with self.assertRaises(ResourceIdentityError):
                service_class_name(tag, "ApiService")
        expected = {service_class_name(tag, "ApiService") for tag in tagged - outside}
        # An untagged operation is generated into "ApiApiService"; the rule refuses it.
        self.assertEqual(expected, generated - {"ApiApiService", "MyTagXApiService"})

    def test_the_reviewed_contract_has_one_resource_named_v1(self) -> None:
        document = load_document(FIXTURES / "gardens.schema.yaml")
        generated = _generated("gardens.services.json")

        identities = {
            subject: resource_identity(subject, document)
            for subject in (
                "path:/api/v1/auth/register/",
                "path:/api/v1/auth/me/",
                "operation:GET /api/v1/auth/me/",
            )
        }

        self.assertEqual({i.resource for i in identities.values()}, {"v1"})
        self.assertEqual({i.api_service for i in identities.values()}, generated)
        self.assertEqual(generated, {"V1ApiService"})


class RuleTests(unittest.TestCase):
    def document(self, **paths):
        return {"paths": paths}

    def test_the_suffix_is_the_generator_service_suffix(self) -> None:
        self.assertEqual(service_class_name("users", "Service"), "UsersService")

    def test_an_untagged_operation_has_no_resource(self) -> None:
        document = self.document(**{"/a": {"get": {}}})
        with self.assertRaisesRegex(ResourceIdentityError, "no tag"):
            resource_identity("path:/a", document)

    def test_several_tags_on_an_operation_have_no_single_resource(self) -> None:
        document = self.document(**{"/a": {"get": {"tags": ["x", "y"]}}})
        with self.assertRaisesRegex(ResourceIdentityError, "several tags"):
            resource_identity("operation:GET /a", document)

    def test_a_path_with_operations_of_two_tags_is_ambiguous(self) -> None:
        document = self.document(
            **{"/a": {"get": {"tags": ["x"]}, "post": {"tags": ["y"]}}}
        )
        with self.assertRaisesRegex(ResourceIdentityError, "2 tags"):
            resource_identity("path:/a", document)
        self.assertEqual(resource_identity("operation:POST /a", document).resource, "y")

    def test_a_tag_the_names_do_not_agree_on_is_refused(self) -> None:
        document = self.document(**{"/a": {"get": {"tags": ["my tag"]}}})
        with self.assertRaisesRegex(ResourceIdentityError, "not a name"):
            resource_identity("path:/a", document)

    def test_a_subject_the_document_lacks_is_distinguished(self) -> None:
        with self.assertRaises(SubjectNotInDocument):
            resource_identity("path:/a", self.document())

    def test_a_schema_subject_has_no_resource(self) -> None:
        with self.assertRaises(ResourceIdentityError):
            resource_identity("schema:User", self.document())

    def test_the_binding_names_the_api_service(self) -> None:
        self.assertEqual(
            binding_service("src/app/api/services#V1ApiService"), "V1ApiService"
        )
        with self.assertRaises(ResourceIdentityError):
            binding_service("V1ApiService")


if __name__ == "__main__":
    unittest.main()
