"""The committed fixtures of the end-to-end flow are the output of their generator."""

import unittest

from django_angular3.validation import validate_openui_file
from tests.e2e import generate_fixtures


class EndToEndFixtureTests(unittest.TestCase):
    def test_committed_fixtures_match_the_generator(self) -> None:
        for path, content in generate_fixtures.generated_files().items():
            with self.subTest(path=path.name):
                self.assertEqual(
                    path.read_text(encoding="utf-8"),
                    content,
                    "Run: python -m tests.e2e.generate_fixtures",
                )

    def test_seed_gives_three_pages(self) -> None:
        customers = [
            d
            for d in generate_fixtures.seed_documents()
            if d["model"] == "shop.customer"
        ]
        pages = -(-len(customers) // generate_fixtures.PAGE_SIZE)
        self.assertEqual((len(customers), pages), (25, 3))

    def test_openui_document_is_valid_with_unique_ids(self) -> None:
        self.assertEqual(
            validate_openui_file(generate_fixtures.FIXTURES / "customers.openui.json"),
            [],
        )
        ids: list[str] = []

        def walk(element: dict) -> None:
            ids.append(element["id"])
            for child in element.get("children", []):
                walk(child)

        walk(generate_fixtures.openui_document())
        self.assertEqual(len(ids), len(set(ids)))


if __name__ == "__main__":
    unittest.main()
