from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.urls import URLPattern

app_name: str = "twitch"

urlpatterns: list[URLPattern] = []
