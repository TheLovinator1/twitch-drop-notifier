from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Literal

from django.contrib import messages
from dotenv import load_dotenv
from platformdirs import user_data_dir

logger: logging.Logger = logging.getLogger(__name__)

# Parse a .env file and then load all the variables found as environment variables.
load_dotenv(verbose=True)

# Store data in %APPDATA%/TheLovinator/TTVDrops on Windows and ~/.config/TheLovinator/TTVDrops on Linux.
# Sqlite database and images will be stored here.
DATA_DIR = Path(
    user_data_dir(
        appname="TTVDrops",
        appauthor="TheLovinator",
        roaming=True,
        ensure_exists=True,
    ),
)

# Default to DEBUG=True if not set.
# Turn off with DEBUG=False in .env file or environment variable.
DEBUG: bool = os.getenv(key="DEBUG", default="True").lower() == "true"

# The base directory of the project.
BASE_DIR: Path = Path(__file__).resolve().parent.parent

# A list of all the people who get code error notifications. When DEBUG=False and AdminEmailHandler is configured in
# LOGGING (done by default), Django emails these people the details of exceptions raised in the request/response cycle.
ADMINS: list[tuple[str, str]] = [("Joakim Hellsén", "tlovinator@gmail.com")]

# The full Python path of the WSGI application object that Django's built-in servers (e.g. runserver) will use.
WSGI_APPLICATION = "core.wsgi.application"

# A secret key for a particular Django installation. This is used to provide cryptographic signing,
# and should be set to a unique, unpredictable value.
SECRET_KEY: str = os.getenv("DJANGO_SECRET_KEY", default="")

# A string representing the full Python import path to your root URLconf
ROOT_URLCONF = "core.urls"

# URL to use when referring to static files located in STATIC_ROOT.
STATIC_URL = "static/"

# Default primary key field type to use for models that don't have a field with primary_key=True.
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# This setting defines the additional locations the staticfiles app will traverse if the FileSystemFinder finder is
# enabled, e.g. if you use the "collectstatic" or "findstatic" management command or use the static file serving view.
STATICFILES_DIRS: list[Path] = [
    BASE_DIR / "static",
]

# The absolute path to the directory where collectstatic will collect static files for deployment.
STATIC_ROOT: Path = BASE_DIR / "staticfiles"
STATIC_ROOT.mkdir(exist_ok=True)  # Create the directory if it doesn't exist.

# URL that handles the media served from MEDIA_ROOT, used for managing stored files.
# It must end in a slash if set to a non-empty value.
MEDIA_URL = "/media/"

# Absolute filesystem path to the directory that will hold user-uploaded files.
MEDIA_ROOT: Path = DATA_DIR / "media"
MEDIA_ROOT.mkdir(exist_ok=True)  # Create the directory if it doesn't exist.

# The model to use to represent a User.
# ! You cannot change the AUTH_USER_MODEL setting during the lifetime of a project
# ! (i.e. once you have made and migrated models that depend on it) without serious effort.
# ! It is intended to be set at the project start, and the model it refers to must be available
# ! in the first migration of the app that it lives in.
AUTH_USER_MODEL: Literal["core.User"] = "core.User"

if DEBUG:
    # A list of IP addresses, as strings, that:
    # - Allow the debug() context processor to add some variables to the template context.
    # - Can use the admindocs bookmarklets even if not logged in as a staff user.
    # - Are marked as “internal” (as opposed to “EXTERNAL”) in AdminEmailHandler emails.

    # This is needed for the Django Debug Toolbar to work.
    INTERNAL_IPS: list[str] = ["127.0.0.1", "192.168.1.129"]

if not DEBUG:
    # List of strings representing the host/domain names that this Django site can serve
    ALLOWED_HOSTS: list[str] = ["ttvdrops.lovinator.space", "localhost"]

# The host to use for sending email.
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER: str | None = os.getenv(key="EMAIL_HOST_USER", default=None)
EMAIL_HOST_PASSWORD: str | None = os.getenv(key="EMAIL_HOST_PASSWORD", default=None)
EMAIL_SUBJECT_PREFIX = "[TTVDrops] "
EMAIL_USE_LOCALTIME = True
EMAIL_TIMEOUT = 10
DEFAULT_FROM_EMAIL: str | None = os.getenv(key="EMAIL_HOST_USER", default=None)
SERVER_EMAIL: str | None = os.getenv(key="EMAIL_HOST_USER", default=None)

# Discord webhook URL for sending notifications.
DISCORD_WEBHOOK_URL: str = os.getenv(key="DISCORD_WEBHOOK_URL", default="")

# The list of all installed applications that Django knows about.
# Be sure to add pghistory.admin above the django.contrib.admin, otherwise the custom admin templates won't be used.
INSTALLED_APPS: list[str] = [
    "core.apps.CoreConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "debug_toolbar",
]

# Middleware is a framework of hooks into Django's request/response processing.
# https://docs.djangoproject.com/en/dev/topics/http/middleware/
MIDDLEWARE: list[str] = [
    "django.middleware.gzip.GZipMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

# Settings for the template engine.
TEMPLATES: list[dict[str, str | list[Path] | bool | dict[str, list[str] | list[tuple[str, list[str]]]]]] = [
    {
        # Use the Django template backend instead of Jinja2.
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # Directories where the engine should look for template source files, in search order.
        "DIRS": [BASE_DIR / "templates"],
        # Whether the engine should look for template source files inside installed applications.
        "APP_DIRS": True,
        # Extra parameters to pass to the template backend.
        # https://docs.djangoproject.com/en/dev/topics/templates/#django.template.backends.django.DjangoTemplates
        "OPTIONS": {
            # Callables that are used to populate the context when a template is rendered with a request.
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.i18n",
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES: dict[str, dict[str, str | Path | dict[str, str | int]]] = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DATA_DIR / "db.sqlite3",
        "OPTIONS": {
            "transaction_mode": "IMMEDIATE",
            "timeout": 5,
            "init_command": """
            PRAGMA journal_mode=WAL;
            PRAGMA synchronous=NORMAL;
            PRAGMA mmap_size=134217728;
            PRAGMA journal_size_limit=27103364;
            PRAGMA cache_size=2000;
            """,
        },
    },
}


LOGGING: dict[str, int | bool | dict[str, dict[str, str | list[str] | bool]]] = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": True,
        },
        "django.utils.autoreload": {  # Remove spam
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
    },
}

# Bootstrap alert classes for Django messages
MESSAGE_TAGS: dict[int, str] = {
    messages.DEBUG: "alert-info",
    messages.INFO: "alert-info",
    messages.SUCCESS: "alert-success",
    messages.WARNING: "alert-warning",
    messages.ERROR: "alert-danger",
}

# The ID, as an integer, of the current site in the django_site database table.
# This is used so that application data can hook into specific sites and a
# single database can manage content for multiple sites.
SITE_ID = 1

# The URL or named URL pattern where requests are redirected after login when the LoginView doesn't
# get a next GET parameter. Defaults to /accounts/profile/.
LOGIN_REDIRECT_URL = "/"

# The URL or named URL pattern where requests are redirected after logout if LogoutView doesn't have
# a next_page attribute.
LOGOUT_REDIRECT_URL = "/"
