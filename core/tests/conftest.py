from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from django.conf import LazySettings

logger: logging.Logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def _media_root(
    settings: LazySettings,
    tmpdir_factory: pytest.TempPathFactory,
) -> None:
    """Forces django to save media files into temp folder."""
    settings.MEDIA_ROOT = tmpdir_factory.mktemp("media", numbered=True)
    logger.info("Testing: Media root is set to %s", settings.MEDIA_ROOT)


@pytest.fixture(autouse=True)
def _password_hashers(settings: LazySettings) -> None:
    """Forces django to use fast password hashers for tests."""
    settings.PASSWORD_HASHERS = [
        "django.contrib.auth.hashers.MD5PasswordHasher",
    ]
    logger.info("Testing: Password hashers are set to %s", settings.PASSWORD_HASHERS)


@pytest.fixture(autouse=True)
def _debug(settings: LazySettings) -> None:
    """Sets proper DEBUG and TEMPLATE debug mode for coverage."""
    settings.DEBUG = False
    for template in settings.TEMPLATES:
        template["OPTIONS"]["debug"] = True

    logger.info("Testing: DEBUG is set to %s", settings.DEBUG)
