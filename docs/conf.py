"""Sphinx configuration for django-angular3."""

import os
import sys

import django
from django.conf import settings

# Make the project root importable so autodoc can find django_angular3.
sys.path.insert(0, os.path.abspath(".."))

# Configure Django minimally so autodoc can import management commands and
# other modules that call django.apps.registry or django.conf.settings.
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "django.contrib.auth",
            "django_angular3",
        ],
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
    )
    django.setup()

# ---------------------------------------------------------------------------
# Project information
# ---------------------------------------------------------------------------
project = "django-angular3"
copyright = "2024, shlomoa"
author = "shlomoa"
release = "0.1.0a1"

# ---------------------------------------------------------------------------
# General configuration
# ---------------------------------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# Accept both .rst and .md source files.
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# MyST Parser extensions used in the narrative docs.
myst_enable_extensions = [
    "colon_fence",
    "deflist",
]

# ---------------------------------------------------------------------------
# HTML output
# ---------------------------------------------------------------------------
html_theme = "furo"
html_static_path = ["_static"]

# ---------------------------------------------------------------------------
# Autodoc
# ---------------------------------------------------------------------------
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
}
autodoc_typehints = "description"
