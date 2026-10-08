"""Locate the ``angular-django2`` (ngdj) source tree for the contract tests.

The tests that compare ``djng`` with the real ngdj source read it from the
repository root named by ``ANGULAR_DJANGO2_ROOT``, or from the sibling checkout
``../angular-django2`` when the variable is unset. Without the source they skip,
unless ``DJNG_REQUIRE_NGDJ=1`` is set (as in the ``ngdj-contract`` CI job), which
turns a missing source into a failure.
"""

from __future__ import annotations

import os
import unittest
from pathlib import Path

ROOT: Path = Path(__file__).resolve().parent.parent
NGDJ_ROOT_ENV = "ANGULAR_DJANGO2_ROOT"
REQUIRE_NGDJ_ENV = "DJNG_REQUIRE_NGDJ"


def ngdj_root() -> Path:
    """Return the ngdj repository root: the environment override or the sibling."""
    override = os.environ.get(NGDJ_ROOT_ENV, "").strip()
    return Path(override) if override else ROOT.parent / "angular-django2"


def ngdj_package_dir() -> Path:
    """Return the ngdj package directory (``projects/angular-django2``)."""
    return ngdj_root() / "projects" / "angular-django2"


def ngdj_required() -> bool:
    """Return whether a missing ngdj source must fail instead of skipping."""
    return os.environ.get(REQUIRE_NGDJ_ENV, "").strip() == "1"


NGDJ_PACKAGE_DIR: Path = ngdj_package_dir()


def require_ngdj_source[T: type[unittest.TestCase]](cls: T) -> T:
    """Skip ``cls`` without the ngdj source, or fail when ``DJNG_REQUIRE_NGDJ=1``."""
    inherited = cls.setUpClass

    def setUpClass(klass: type[unittest.TestCase]) -> None:
        if not NGDJ_PACKAGE_DIR.is_dir():
            message = (
                f"angular-django2 source not found at {NGDJ_PACKAGE_DIR}; "
                f"set {NGDJ_ROOT_ENV} or check it out next to this repository"
            )
            if ngdj_required():
                raise AssertionError(f"{REQUIRE_NGDJ_ENV}=1: {message}")
            raise unittest.SkipTest(message)
        inherited()

    cls.setUpClass = classmethod(setUpClass)  # type: ignore[method-assign]
    return cls
