"""Local development settings."""

from .base import *  # noqa: F403

DEBUG = True

# Allow all hosts in dev only if explicitly requested (e.g. Docker hostname).
if env.bool("ALLOW_ALL_HOSTS_DEV", default=False):  # noqa: F405
    ALLOWED_HOSTS = ["*"]  # noqa: F405
