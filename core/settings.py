import os
from pathlib import Path

import sentry_sdk
from dotenv import find_dotenv, load_dotenv

# Load environment variables from a .env file
load_dotenv(dotenv_path=find_dotenv(), verbose=True)

# Run Django in debug mode
DEBUG: bool = os.getenv(key="DEBUG", default="True").lower() == "true"

# Use Sentry for error reporting
USE_SENTRY: bool = os.getenv(key="USE_SENTRY", default="True").lower() == "true"
if USE_SENTRY:
    sentry_sdk.init(
        dsn="https://35519536b56710e51cac49522b2cc29f@o4505228040339456.ingest.sentry.io/4506447308914688",
        environment="Development" if DEBUG else "Production",
        send_default_pii=True,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR: Path = Path(__file__).resolve().parent.parent

# A list of all the people who get code error notifications. When DEBUG=False and a view raises an exception, Django
ADMINS: list[tuple[str, str]] = [
    ("Joakim Hellsén", os.getenv("ADMIN_EMAIL", default="")),
]

# The secret key is used for cryptographic signing, and should be set to a unique, unpredictable value.
SECRET_KEY: str = os.getenv("SECRET_KEY", default="")

# A list of strings representing the host/domain names that this Django site can serve.
ALLOWED_HOSTS: list[str] = [
    "ttvdrops.lovinator.space",
    ".localhost",
    "127.0.0.1",
]

# The time zone that Django will use to display datetimes in templates and to interpret datetimes entered in forms
TIME_ZONE = "Europe/Stockholm"

# If datetimes will be timezone-aware by default. If True, Django will use timezone-aware datetimes internally.
USE_TZ = True

# Decides which translation is served to all users.
LANGUAGE_CODE = "en-us"

# Default decimal separator used when formatting decimal numbers.
DECIMAL_SEPARATOR = ","

# Use a space as the thousand separator instead of a comma
THOUSAND_SEPARATOR = " "

# Use gmail for sending emails
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER: str = os.getenv(key="EMAIL_HOST_USER", default="webmaster@localhost")
EMAIL_HOST_PASSWORD: str = os.getenv(key="EMAIL_HOST_PASSWORD", default="")
EMAIL_SUBJECT_PREFIX = "[Panso] "
EMAIL_USE_LOCALTIME = True
EMAIL_TIMEOUT = 10
DEFAULT_FROM_EMAIL: str = os.getenv(
    key="EMAIL_HOST_USER",
    default="webmaster@localhost",
)
SERVER_EMAIL: str = os.getenv(key="EMAIL_HOST_USER", default="webmaster@localhost")

INSTALLED_APPS: list[str] = [
    # First-party apps
    "twitch_drop_notifier.apps.TwitchDropNotifierConfig",
    # Third-party apps
    "whitenoise.runserver_nostatic",
    # Django apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
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
]

ROOT_URLCONF = "core.urls"

# A list containing the settings for all template engines to be used with Django.
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

WSGI_APPLICATION = "core.wsgi.application"

# A dictionary containing the settings for how we should connect to our PostgreSQL database.
DATABASES: dict[str, dict[str, str]] = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "ttvdrops",
        "USER": os.getenv(key="POSTGRES_USER", default=""),
        "PASSWORD": os.getenv(key="POSTGRES_PASSWORD", default=""),
        "HOST": os.getenv(key="POSTGRES_HOST", default=""),
        "PORT": os.getenv(key="POSTGRES_PORT", default="5432"),
    },
}


# URL to use when referring to static files located in STATIC_ROOT.
STATIC_URL = "static/"


# Use a 64-bit integer as a primary key for models that don't have a field with primary_key=True.
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# The absolute path to the directory where 'python manage.py collectstatic' will copy static files for deployment
STATIC_ROOT: Path = BASE_DIR / "staticfiles"
STATICFILES_DIRS: list[Path] = [BASE_DIR / "static"]


# Use WhiteNoise to serve static files. https://whitenoise.readthedocs.io/en/latest/django.html
STORAGES: dict[str, dict[str, str]] = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


# Use Redis for caching
REDIS_PASSWORD: str = os.getenv(key="REDIS_PASSWORD", default="")
REDIS_HOST: str = os.getenv(key="REDIS_HOST", default="")
REDIS_PORT: str = os.getenv(key="REDIS_PORT", default="6380")
CACHES: dict[str, dict[str, str]] = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0",
    },
}
