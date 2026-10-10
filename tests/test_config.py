"""Tests of values calculated from the project configuration."""

import json
import tempfile
import unittest
from pathlib import Path

from django_angular3.config import load_project_config
from tests.workspace_temp import WORKSPACE_TEMP_DIR

FIXTURE = Path(__file__).parent / "fixtures" / "django-angular3-project.json"


class AngularDistTests(unittest.TestCase):
    def test_bundle_is_calculated_from_workspace_and_project_name(self) -> None:
        config = load_project_config(FIXTURE)

        self.assertEqual(
            config.angular_dist,
            config.angular_workspace / "dist" / config.project_name / "browser",
        )

    def test_bundle_follows_the_configuration_that_selects_the_workspace(self) -> None:
        with tempfile.TemporaryDirectory(dir=WORKSPACE_TEMP_DIR) as temporary:
            root = Path(temporary)
            path = root / "django-angular3-shop.json"
            path.write_text(
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

            config = load_project_config(path)

            self.assertEqual(
                config.angular_dist,
                (root / "frontend" / "ng" / "dist" / "shop" / "browser").resolve(),
            )


if __name__ == "__main__":
    unittest.main()
