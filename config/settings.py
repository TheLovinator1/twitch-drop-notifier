import os
from pathlib import Path

import sentry_sdk
from django.contrib import messages
from dotenv import find_dotenv, load_dotenv
from platformdirs import user_data_dir

load_dotenv(dotenv_path=find_dotenv(), verbose=True)


DATA_DIR = Path(
    user_data_dir(
        appname="TTVDrops",
        appauthor="TheLovinator",
        roaming=True,
        ensure_exists=True,
    ),
)

DEBUG: bool = os.getenv(key="DEBUG", default="True").lower() == "true"

sentry_sdk.init(
    dsn="https://35519536b56710e51cac49522b2cc29f@o4505228040339456.ingest.sentry.io/4506447308914688",
    environment="Development" if DEBUG else "Production",
    send_default_pii=True,
    traces_sample_rate=0.2,
    profiles_sample_rate=0.2,
)


BASE_DIR: Path = Path(__file__).resolve().parent.parent
ADMINS: list[tuple[str, str]] = [("Joakim Hellsén", "tlovinator@gmail.com")]
WSGI_APPLICATION = "config.wsgi.application"
SECRET_KEY: str = os.getenv("DJANGO_SECRET_KEY", default="")
TIME_ZONE = "Europe/Stockholm"
USE_TZ = True
LANGUAGE_CODE = "en-us"
DECIMAL_SEPARATOR = ","
THOUSAND_SEPARATOR = " "
ROOT_URLCONF = "config.urls"
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
STATICFILES_DIRS: list[Path] = [BASE_DIR / "static"]
STATIC_ROOT: Path = BASE_DIR / "staticfiles"
STATIC_ROOT.mkdir(exist_ok=True)

if not DEBUG:
    ALLOWED_HOSTS: list[str] = ["ttvdrops.lovinator.space"]

EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER: str = os.getenv(key="EMAIL_HOST_USER", default="webmaster@localhost")
EMAIL_HOST_PASSWORD: str = os.getenv(key="EMAIL_HOST_PASSWORD", default="")
EMAIL_SUBJECT_PREFIX = "[TTVDrops] "
EMAIL_USE_LOCALTIME = True
EMAIL_TIMEOUT = 10
DEFAULT_FROM_EMAIL: str = os.getenv(
    key="EMAIL_HOST_USER",
    default="webmaster@localhost",
)
SERVER_EMAIL: str = os.getenv(key="EMAIL_HOST_USER", default="webmaster@localhost")
DISCORD_WEBHOOK_URL: str = os.getenv(key="DISCORD_WEBHOOK_URL", default="")

INSTALLED_APPS: list[str] = [
    "core.apps.CoreConfig",
    "twitch_app.apps.TwitchConfig",
    "whitenoise.runserver_nostatic",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "ninja",
    "simple_history",
]

MIDDLEWARE: list[str] = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
]


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            "loaders": [
                (
                    "django.template.loaders.cached.Loader",
                    [
                        "django.template.loaders.filesystem.Loader",
                        "django.template.loaders.app_directories.Loader",
                    ],
                ),
            ],
        },
    },
]

# Don't cache templates in development
if DEBUG:
    TEMPLATES[0]["OPTIONS"]["loaders"] = [
        "django.template.loaders.filesystem.Loader",
        "django.template.loaders.app_directories.Loader",
    ]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DATA_DIR / "ttvdrops.sqlite3",
        "OPTIONS": {
            # "init_command": "PRAGMA journal_mode=wal; PRAGMA synchronous=1; PRAGMA mmap_size=134217728; PRAGMA journal_size_limit=67108864; PRAGMA cache_size=2000;",  # noqa: E501
        },
    },
}

STORAGES: dict[str, dict[str, str]] = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

LOGGING = {
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

MESSAGE_TAGS: dict[int, str] = {
    messages.DEBUG: "alert-info",
    messages.INFO: "alert-info",
    messages.SUCCESS: "alert-success",
    messages.WARNING: "alert-warning",
    messages.ERROR: "alert-danger",
}
