#!/usr/bin/env python
import os
from rallytap.scripts import env


if __name__ == '__main__':
    # Export our environment variables.
    env.read_env()

    environ = os.environ['ENV']
    settings_module = 'rallytap.settings.{environ}'.format(environ=environ)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)

    from django.core.management import execute_from_command_line

    execute_from_command_line(os.sys.argv)
