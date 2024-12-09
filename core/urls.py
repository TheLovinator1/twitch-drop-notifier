from __future__ import annotations

from debug_toolbar.toolbar import debug_toolbar_urls  # type: ignore[import-untyped]
from django.contrib import admin
from django.urls import URLPattern, URLResolver, path

from core.views import game_view, games_view, index, reward_campaign_view

app_name: str = "core"

urlpatterns: list[URLPattern | URLResolver] = [
    path(route="admin/", view=admin.site.urls),
    path(route="", view=index, name="index"),
    path(route="game/<int:twitch_id>/", view=game_view, name="game"),
    path(route="games/", view=games_view, name="games"),
    path(route="reward_campaigns/", view=reward_campaign_view, name="reward_campaigns"),
    *debug_toolbar_urls(),
]
