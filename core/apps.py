from __future__ import annotations

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Core app configuration."""

    default_auto_field: str = "django.db.models.BigAutoField"
    name = "core"
