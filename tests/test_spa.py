"""Tests of the view that serves the built Angular application from Django.

Every test builds a project directory of its own: the project configuration, the tool
configuration and a browser output directory, so the view is exercised on the real
configuration calculation and nothing is set in the Django settings.
"""

import copy
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import django
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings

from django_angular3.settings import PACKAGE_DEFAULT_CONFIG_PATH

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.test_settings")
django.setup()

INDEX_HTML = '<!doctype html><html><head><base href="/"></head><body>app</body></html>'
OUTPUT = "out/shop/browser"
PACKAGED = json.loads(PACKAGE_DEFAULT_CONFIG_PATH.read_text(encoding="utf-8"))


def write_project(
    root: Path, *, output: str | None = OUTPUT, tool_configuration: bool = True
) -> Path:
    """Write a ``shop`` project under ``root``; return its browser output directory.

    ``output`` is the ``angular.build.browserOutputPath`` of the tool configuration,
    left out when ``None``.
    """
    (root / "django-angular3-shop.json").write_text(
        json.dumps(
            {
                "project": {"name": "shop"},
                "artifacts": {
                    "openapiSchema": "schema.json",
                    "openuiSpecification": "app.openui.json",
                    "angularWorkspace": "frontend/ng",
                },
            }
        ),
        encoding="utf-8",
    )
    if tool_configuration:
        tool = copy.deepcopy(PACKAGED)
        if output is None:
            del tool["angular"]["build"]["browserOutputPath"]
        else:
            tool["angular"]["build"]["browserOutputPath"] = output
        (root / "django-angular3.json").write_text(json.dumps(tool), encoding="utf-8")
    return root / "frontend" / "ng" / (output or OUTPUT)


def build(directory: Path) -> None:
    """Leave a browser output like the one ``ng_build`` leaves."""
    directory.mkdir(parents=True)
    (directory / "index.html").write_text(INDEX_HTML, encoding="utf-8")
    (directory / "main-ABC123.js").write_text("console.log(1);", encoding="utf-8")
    (directory / "styles-XYZ789.css").write_text("body{}", encoding="utf-8")


class ProjectTestCase(SimpleTestCase):
    """Runs a test inside a project directory found from ``settings.BASE_DIR``."""

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        override = override_settings(ROOT_URLCONF="tests.spa_urls", BASE_DIR=self.root)
        override.enable()
        self.addCleanup(override.disable)
        environment = patch.dict(
            os.environ, {"DJANGO_SETTINGS_MODULE": "shop.settings"}
        )
        environment.start()
        self.addCleanup(environment.stop)

    def fetch(self, path: str, **extra: object):
        """GET ``path`` and close the file the response streams when the test ends."""
        response = self.client.get(path, **extra)
        self.addCleanup(response.close)
        return response


class AngularAppViewTests(ProjectTestCase):
    def setUp(self) -> None:
        super().setUp()
        build(write_project(self.root))
        (self.root / "secret.txt").write_text("secret")

    def test_root_serves_index_html(self) -> None:
        response = self.fetch("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response["Content-Type"])
        self.assertEqual(b"".join(response.streaming_content).decode(), INDEX_HTML)

    def test_assets_are_served_with_their_content_type(self) -> None:
        script = self.fetch("/main-ABC123.js")
        self.assertEqual(script.status_code, 200)
        self.assertIn("javascript", script["Content-Type"])
        style = self.fetch("/styles-XYZ789.css")
        self.assertEqual(style.status_code, 200)
        self.assertIn("text/css", style["Content-Type"])

    def test_unknown_application_route_falls_back_to_index_html(self) -> None:
        for route in ("/customers", "/customers/", "/customers/42/edit"):
            with self.subTest(route=route):
                response = self.fetch(route)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    b"".join(response.streaming_content).decode(), INDEX_HTML
                )

    def test_missing_asset_is_a_404_not_index_html(self) -> None:
        self.assertEqual(self.fetch("/main-OLDHASH.js").status_code, 404)
        self.assertEqual(self.fetch("/missing/chunk.css").status_code, 404)

    def test_django_routes_declared_before_the_view_win(self) -> None:
        self.assertEqual(self.fetch("/api/v1/ping/").json(), {"ok": True})

    def test_unmatched_reserved_prefixes_are_404_not_index_html(self) -> None:
        for route in ("/api/v1/nope/", "/admin/nope/", "/static/nope", "/api-auth/x"):
            with self.subTest(route=route):
                self.assertEqual(self.fetch(route).status_code, 404)

    def test_path_traversal_is_refused(self) -> None:
        for route in ("/../secret.txt", "/%2e%2e/secret.txt", "/..%2fsecret.txt"):
            with self.subTest(route=route):
                self.assertNotEqual(self.fetch(route).status_code, 200, route)

    def test_only_get_and_head_are_allowed(self) -> None:
        head = self.client.head("/customers")
        self.addCleanup(head.close)
        self.assertEqual(head.status_code, 200)
        self.assertEqual(self.client.post("/customers").status_code, 405)

    def test_conditional_get_is_answered_with_304(self) -> None:
        first = self.fetch("/main-ABC123.js")
        second = self.fetch(
            "/main-ABC123.js", headers={"If-Modified-Since": first["Last-Modified"]}
        )
        self.assertEqual(second.status_code, 304)


class AngularAppViewConfigurationTests(ProjectTestCase):
    """What is missing is reported, not answered with a silent 404."""

    def test_the_directory_is_the_workspace_plus_the_configured_path(self) -> None:
        build(write_project(self.root, output="other/place/browser"))

        self.assertEqual(self.fetch("/customers").status_code, 200)

    def test_the_setting_is_mandatory(self) -> None:
        build(write_project(self.root, output=None))

        with self.assertRaisesRegex(ImproperlyConfigured, "browserOutputPath"):
            self.client.get("/customers")

    def test_the_tool_configuration_is_needed(self) -> None:
        write_project(self.root, tool_configuration=False)

        with self.assertRaisesRegex(ImproperlyConfigured, "browserOutputPath"):
            self.client.get("/customers")

    def test_the_project_configuration_is_needed(self) -> None:
        with self.assertRaisesRegex(ImproperlyConfigured, "django-angular3-shop.json"):
            self.client.get("/customers")

    def test_missing_directory_names_the_path_and_the_build_command(self) -> None:
        directory = write_project(self.root)

        with self.assertRaises(ImproperlyConfigured) as raised:
            self.client.get("/customers")

        self.assertIn(str(directory.resolve()), str(raised.exception))
        self.assertIn("ng_build", str(raised.exception))

    def test_directory_without_index_html_is_reported(self) -> None:
        write_project(self.root).mkdir(parents=True)

        with self.assertRaisesRegex(ImproperlyConfigured, "index.html"):
            self.client.get("/")


if __name__ == "__main__":
    unittest.main()
