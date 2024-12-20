#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

from __future__ import annotations

import os
import sys

try:
    from django.core.management import execute_from_command_line
except ImportError as exc:
    msg = (
        "Couldn't import Django. Are you sure it's installed and "
        "available on your PYTHONPATH environment variable? Did you "
        "forget to activate a virtual environment?"
    )
    raise ImportError(msg) from exc


def main() -> None:
    """Run administrative tasks."""
    os.environ.setdefault(key="DJANGO_SETTINGS_MODULE", value="core.settings")
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
