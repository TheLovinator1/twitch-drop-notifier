from __future__ import annotations

from django.urls import URLPattern, URLResolver, path

from . import views

app_name: str = "core"


urlpatterns: list[URLPattern | URLResolver] = [
    path(route="", view=views.index, name="index"),
]
