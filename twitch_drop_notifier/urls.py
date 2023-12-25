from __future__ import annotations

from django.urls import URLPattern, path
from django.views.generic.base import RedirectView

from . import views

app_name: str = "twitch_drop_notifier"

urlpatterns: list[URLPattern] = [
    path(route="", view=views.index, name="index"),
    path(route="privacy", view=views.privacy, name="privacy"),
    path(route="terms", view=views.terms, name="terms"),
    path(route="contact", view=views.contact, name="contact"),
    path(route="robots.txt", view=views.robots_txt, name="robots-txt"),
    path(
        route="favicon.ico",
        view=RedirectView.as_view(url="/static/favicon.ico", permanent=True),
    ),
    path(
        route="icon-512.png",
        view=RedirectView.as_view(url="/static/icon-512.png", permanent=True),
    ),
    path(
        route="icon-192.png",
        view=RedirectView.as_view(url="/static/icon-192.png", permanent=True),
    ),
]
