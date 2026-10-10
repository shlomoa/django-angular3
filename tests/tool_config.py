"""The tool configuration the tests run with.

``django-angular3.json`` is mandatory and has no runtime fallback. Tests that run the
commands without a project of their own use the packaged template, the file that
``install-tutorial`` copies, as their tool configuration: ``setUpModule`` calls
``use_tool_configuration_template`` so that discovery finds it.
"""

import json
import unittest
from unittest.mock import patch

from django_angular3.settings import TOOL_CONFIG_TEMPLATE_PATH

TEMPLATE = json.loads(TOOL_CONFIG_TEMPLATE_PATH.read_text(encoding="utf-8"))
NG_ADD_PACKAGE: str = TEMPLATE["tool"]["ngAddPackage"]


def use_tool_configuration_template() -> None:
    """Discover the packaged template as the tool configuration, for one test module."""
    patcher = patch(
        "django_angular3.settings.discover_tool_config_path",
        return_value=TOOL_CONFIG_TEMPLATE_PATH,
    )
    patcher.start()
    unittest.addModuleCleanup(patcher.stop)
