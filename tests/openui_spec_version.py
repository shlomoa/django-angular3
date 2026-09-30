"""The openui-spec version under test, read from the installed package.

The package version equals the spec version it implements, so a document
``version`` and the ``pyproject.toml`` pin never repeat it in test code.
"""

from importlib.metadata import version

OPENUI_SPEC_VERSION = version("openui-spec")
