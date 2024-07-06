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
    path("webhooks/", views.WebhooksView.as_view(), name="webhooks"),
]
