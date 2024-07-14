from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import hishel
from django.conf import settings
from django.contrib import messages
from django.http.response import HttpResponse
from django.views.generic import FormView

from core.data import WebhookData
from core.forms import DiscordSettingForm
from twitch_app.models import Game

if TYPE_CHECKING:
    from pathlib import Path

    from django.http import HttpRequest


cache_dir: Path = settings.DATA_DIR / "cache"
cache_dir.mkdir(exist_ok=True, parents=True)
storage = hishel.FileStorage(base_path=cache_dir)
controller = hishel.Controller(
    cacheable_status_codes=[200, 203, 204, 206, 300, 301, 308, 404, 405, 410, 414, 501],
    allow_stale=True,
    always_revalidate=True,
)


if TYPE_CHECKING:
    from django.http import (
        HttpResponse,
    )
    from httpx import Response

logger: logging.Logger = logging.getLogger(__name__)


def get_webhooks(request: HttpRequest) -> list[str]:
    """Get the webhooks from the cookie."""
    cookie: str = request.COOKIES.get("webhooks", "")
    return list(filter(None, cookie.split(",")))


def get_avatar(webhook_response: Response) -> str:
    """Get the avatar URL from the webhook response."""
    avatar: str = "https://cdn.discordapp.com/embed/avatars/0.png"
    if webhook_response.is_success and webhook_response.json().get("id") and webhook_response.json().get("avatar"):
        avatar = f'https://cdn.discordapp.com/avatars/{webhook_response.json().get("id")}/{webhook_response.json().get("avatar")}.png'
    return avatar


def get_webhook_data(webhook: str) -> WebhookData:
    """Get the webhook data."""
    with hishel.CacheClient(storage=storage, controller=controller) as client:
        webhook_response: Response = client.get(url=webhook, extensions={"cache_metadata": True})

    return WebhookData(
        name=webhook_response.json().get("name") if webhook_response.is_success else "Unknown",
        url=webhook,
        avatar=get_avatar(webhook_response),
        status="Success" if webhook_response.is_success else "Failed",
        response=webhook_response.text,
    )


class WebhooksView(FormView):
    model = Game
    template_name = "webhooks.html"
    form_class = DiscordSettingForm
    context_object_name: str = "webhooks"
    paginate_by = 100

    def get_context_data(self: WebhooksView, **kwargs: dict[str, WebhooksView] | DiscordSettingForm) -> dict[str, Any]:
        """Get the context data for the view."""
        context: dict[str, DiscordSettingForm | list[WebhookData]] = super().get_context_data(**kwargs)
        webhooks: list[str] = get_webhooks(self.request)

        context.update({
            "webhooks": [get_webhook_data(webhook) for webhook in webhooks],
            "form": DiscordSettingForm(),
        })
        return context

    def form_valid(self: WebhooksView, form: DiscordSettingForm) -> HttpResponse:
        """Handle valid form submission."""
        webhook = str(form.cleaned_data["webhook_url"])

        with hishel.CacheClient(storage=storage, controller=controller) as client:
            webhook_response: Response = client.get(url=webhook, extensions={"cache_metadata": True})
            if not webhook_response.is_success:
                messages.error(self.request, "Failed to get webhook information. Is the URL correct?")
                return self.render_to_response(self.get_context_data(form=form))

        webhook_name: str | None = str(webhook_response.json().get("name")) if webhook_response.is_success else None

        cookie: str = self.request.COOKIES.get("webhooks", "")
        webhooks: list[str] = cookie.split(",")
        webhooks = list(filter(None, webhooks))
        if webhook in webhooks:
            if webhook_name:
                messages.error(self.request, f"Webhook {webhook_name} already exists.")
            else:
                messages.error(self.request, "Webhook already exists.")
            return self.render_to_response(self.get_context_data(form=form))

        webhooks.append(webhook)
        response: HttpResponse = self.render_to_response(self.get_context_data(form=form))
        response.set_cookie(key="webhooks", value=",".join(webhooks), max_age=315360000)  # 10 years

        messages.success(self.request, "Webhook successfully added.")
        return response

    def form_invalid(self: WebhooksView, form: DiscordSettingForm) -> HttpResponse:
        messages.error(self.request, "Failed to add webhook.")
        return self.render_to_response(self.get_context_data(form=form))
