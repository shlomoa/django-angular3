from html.parser import HTMLParser
from pathlib import Path
from unittest import SkipTest, TestCase

REPO_ROOT = Path(__file__).resolve().parents[1]
TUTORIAL_HTML = REPO_ROOT / "docs" / "_build" / "html" / "tutorial.html"
TARGET_URL = (
    "https://github.com/shlomoa/django-angular3/blob/main/"
    "doc/specifications/SPECIFICATIONS.md"
    "#21-configuration-and-input-categories"
)


class _TutorialHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[dict[str, str | None]] = []
        self.scripts: list[dict[str, str | None]] = []
        self.stylesheets: list[dict[str, str | None]] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        attributes = dict(attrs)
        if tag == "a":
            self.links.append(attributes)
        elif tag == "script":
            self.scripts.append(attributes)
        elif tag == "link" and attributes.get("rel") == "stylesheet":
            self.stylesheets.append(attributes)


class TutorialModalLinkDocsTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        if not TUTORIAL_HTML.exists():
            raise SkipTest(
                "Build the Sphinx documentation before running the docs "
                "integration test."
            )

        cls.parser = _TutorialHtmlParser()
        cls.parser.feed(TUTORIAL_HTML.read_text(encoding="utf-8"))

    def test_tutorial_build_includes_modal_link_and_assets(self) -> None:
        modal_links = [
            link
            for link in self.parser.links
            if "modal-link" in (link.get("class") or "").split()
        ]

        self.assertEqual([link.get("href") for link in modal_links], [TARGET_URL])
        self.assertTrue(
            any(
                (script.get("src") or "")
                .split("?", 1)[0]
                .endswith("_static/modal_links.js")
                for script in self.parser.scripts
            )
        )
        self.assertTrue(
            any(
                (stylesheet.get("href") or "")
                .split("?", 1)[0]
                .endswith("_static/custom.css")
                for stylesheet in self.parser.stylesheets
            )
        )
