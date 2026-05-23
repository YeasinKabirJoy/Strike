#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

from dotenv import load_dotenv


load_dotenv()


def env_bool(name):
    return os.environ.get(name, '').strip() == 'True'


if env_bool('PRETTY_ERRORS'):
    import pretty_errors

    pretty_errors.configure(
        display_link=True,
        lines_before=2,
        lines_after=1,
        display_locals=env_bool('PRETTY_ERRORS_SHOW_LOCALS'),
    )


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
