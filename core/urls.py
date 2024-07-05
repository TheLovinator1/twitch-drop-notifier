from __future__ import annotations

from django.urls import URLPattern, URLResolver, path

from . import views

app_name: str = "core"


urlpatterns: list[URLPattern | URLResolver] = [
    path(route="", view=views.index, name="index"),
    path(
        route="games/",
        view=views.GameView.as_view(),
        name="games",
    ),
    path(
        route="webhooks/",
        view=views.Webhooks.as_view(),
        name="webhooks",
    ),
    path(
        route="webhooks/add/",
        view=views.add_webhook,
        name="add_webhook",
    ),
]
