from __future__ import annotations

from django.urls import URLPattern, URLResolver, path

from . import views

app_name: str = "core"


urlpatterns: list[URLPattern | URLResolver] = [
    path(route="", view=views.index, name="index"),
    path(route="test/", view=views.test_webhook, name="test"),
    path(
        route="add-discord-webhook/",
        view=views.add_discord_webhook,
        name="add_discord_webhook",
    ),
    path(
        route="delete_discord_webhook/",
        view=views.delete_discord_webhook,
        name="delete_discord_webhook",
    ),
    path(
        route="subscribe/",
        view=views.subscription_create,
        name="subscription_create",
    ),
    path(
        route="games/",
        view=views.GameView.as_view(),
        name="games",
    ),
]
