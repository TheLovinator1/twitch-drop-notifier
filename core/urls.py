from __future__ import annotations

from django.urls import URLPattern, URLResolver, path

from .views.games import GameView
from .views.index import index
from .views.webhooks import WebhooksView

app_name: str = "core"

urlpatterns: list[URLPattern | URLResolver] = [
    path(route="", view=index, name="index"),
    path(
        route="games/",
        view=GameView.as_view(),
        name="games",
    ),
    path("webhooks/", WebhooksView.as_view(), name="webhooks"),
]
