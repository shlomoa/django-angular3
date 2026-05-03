import os
import unittest

try:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.test_settings")
    import django
    django.setup()
    from django.apps import apps
    from django.test import SimpleTestCase
    DJANGO_AVAILABLE = True
except ImportError:
    DJANGO_AVAILABLE = False
    SimpleTestCase = unittest.TestCase


@unittest.skipUnless(DJANGO_AVAILABLE, "Django is required for smoke tests.")
class AppConfigSmokeTest(SimpleTestCase):
    def test_app_is_registered(self) -> None:
        self.assertTrue(apps.is_installed("django_angular3"))

    def test_app_config_attributes(self) -> None:
        config = apps.get_app_config("django_angular3")
        self.assertEqual(config.name, "django_angular3")
        self.assertEqual(config.default_auto_field, "django.db.models.BigAutoField")
