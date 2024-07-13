import logging

from debug_toolbar.toolbar import debug_toolbar_urls
from django.urls import URLPattern, include, path
from django.urls.resolvers import URLResolver
from ninja import NinjaAPI

from twitch_app.api import router as twitch_router

logger: logging.Logger = logging.getLogger(__name__)

api = NinjaAPI(
    title="TTVDrops API",
    version="1.0.0",
    description="No rate limits, but don't abuse it.",
)

api.add_router(prefix="/twitch", router=twitch_router)

app_name: str = "config"

urlpatterns: list[URLPattern | URLResolver] = [
    path(route="", view=include(arg="core.urls")),
    path(route="api/", view=api.urls),
    *debug_toolbar_urls(),
]
