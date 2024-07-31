from __future__ import annotations

from django.urls import URLPattern, URLResolver, path

from core.views import GameView, RewardCampaignView, index

app_name: str = "core"

urlpatterns: list[URLPattern | URLResolver] = [
    path(route="", view=index, name="index"),
    path(
        route="games/",
        view=GameView.as_view(),
        name="games",
    ),
    path(
        route="reward_campaigns/",
        view=RewardCampaignView.as_view(),
        name="reward_campaigns",
    ),
]
