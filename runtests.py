#! /usr/bin/env python3
import os
import sys


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.test_settings")

    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        from unittest import TextTestRunner, defaultTestLoader

        suite = defaultTestLoader.discover("tests", pattern="test_*.py", top_level_dir=".")
        return 0 if TextTestRunner().run(suite).wasSuccessful() else 1

    execute_from_command_line(["django-admin", "test", "tests", *argv])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
