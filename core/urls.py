from __future__ import annotations

from debug_toolbar.toolbar import debug_toolbar_urls  # type: ignore[import-untyped]
from django.contrib import admin
from django.urls import URLPattern, URLResolver, path

from core.views import get_game, get_games, get_home, get_import

app_name: str = "core"

# TODO(TheLovinator): Add a 404 page and a 500 page.
# https://docs.djangoproject.com/en/dev/topics/http/views/#customizing-error-views

# TODO(TheLovinator): Add a robots.txt file.
# https://developers.google.com/search/docs/crawling-indexing/robots/intro

# TODO(TheLovinator): Add sitemaps
# https://docs.djangoproject.com/en/dev/ref/contrib/sitemaps/

# TODO(TheLovinator): Add a favicon.
# https://docs.djangoproject.com/en/dev/howto/static-files/#serving-files-in-development

# TODO(TheLovinator): Add funding.json
# https://floss.fund/funding-manifest/

# TODO(TheLovinator): Add a humans.txt file.
# https://humanstxt.org/

# TODO(TheLovinator): Add pghistory context when importing JSON.
# https://django-pghistory.readthedocs.io/en/3.5.0/context/#using-pghistorycontext

# The URL patterns for the core app.
urlpatterns: list[URLPattern | URLResolver] = [
    path(route="admin/", view=admin.site.urls),
    path(route="", view=get_home, name="index"),
    path(route="game/<int:twitch_id>/", view=get_game, name="game"),
    path(route="games/", view=get_games, name="games"),
    path(route="import/", view=get_import, name="import"),
    *debug_toolbar_urls(),
]
