"""Tests of the view that serves the built Angular application from Django."""

import os
import tempfile
import unittest
from pathlib import Path

import django
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.test_settings")
django.setup()

INDEX_HTML = '<!doctype html><html><head><base href="/"></head><body>app</body></html>'


class AngularAppViewTests(SimpleTestCase):
    """The view works on a ``dist/<app>/browser`` directory the test builds itself."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls._temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls._temporary.cleanup)
        cls.dist = Path(cls._temporary.name) / "browser"
        cls.dist.mkdir()
        (cls.dist / "index.html").write_text(INDEX_HTML, encoding="utf-8")
        (cls.dist / "main-ABC123.js").write_text("console.log(1);", encoding="utf-8")
        (cls.dist / "styles-XYZ789.css").write_text("body{}", encoding="utf-8")
        (Path(cls._temporary.name) / "secret.txt").write_text("secret")
        cls.override = override_settings(
            ROOT_URLCONF="tests.spa_urls", ANGULAR_DIST_DIR=cls.dist
        )
        cls.override.enable()
        cls.addClassCleanup(cls.override.disable)

    def fetch(self, path: str, **extra: object):
        """GET ``path`` and close the file the response streams when the test ends."""
        response = self.client.get(path, **extra)
        self.addCleanup(response.close)
        return response

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
        response = self.fetch("/api/v1/ping/")
        self.assertEqual(response.json(), {"ok": True})

    def test_unmatched_reserved_prefixes_are_404_not_index_html(self) -> None:
        for route in ("/api/v1/nope/", "/admin/nope/", "/static/nope", "/api-auth/x"):
            with self.subTest(route=route):
                self.assertEqual(self.fetch(route).status_code, 404)

    def test_path_traversal_is_refused(self) -> None:
        for route in ("/../secret.txt", "/%2e%2e/secret.txt", "/..%2fsecret.txt"):
            with self.subTest(route=route):
                response = self.fetch(route)
                self.assertNotEqual(response.status_code, 200, route)

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


class AngularAppViewConfigurationTests(SimpleTestCase):
    """A missing build is reported, not answered with a silent 404."""

    def test_setting_is_required(self) -> None:
        with override_settings(ROOT_URLCONF="tests.spa_urls"):
            with self.assertRaisesRegex(ImproperlyConfigured, "ANGULAR_DIST_DIR"):
                self.client.get("/customers")

    def test_missing_directory_names_the_path_and_the_build_command(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            missing = Path(temporary) / "nowhere"
            with override_settings(
                ROOT_URLCONF="tests.spa_urls", ANGULAR_DIST_DIR=missing
            ):
                with self.assertRaises(ImproperlyConfigured) as raised:
                    self.client.get("/customers")
        self.assertIn(str(missing), str(raised.exception))
        self.assertIn("ng_build", str(raised.exception))

    def test_directory_without_index_html_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with override_settings(
                ROOT_URLCONF="tests.spa_urls", ANGULAR_DIST_DIR=Path(temporary)
            ):
                with self.assertRaisesRegex(ImproperlyConfigured, "index.html"):
                    self.client.get("/")


if __name__ == "__main__":
    unittest.main()
