import logging

from debug_toolbar.toolbar import debug_toolbar_urls
from django.urls import URLPattern, include, path
from django.urls.resolvers import URLResolver

logger: logging.Logger = logging.getLogger(__name__)

app_name: str = "config"

urlpatterns: list[URLPattern | URLResolver] = [
    path(route="", view=include(arg="core.urls")),
    *debug_toolbar_urls(),
]
