from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import hishel
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.template.response import TemplateResponse

from core.data import WebhookData
from twitch_app.models import (
    Organization,
)

if TYPE_CHECKING:
    from pathlib import Path

    from django.db.models.manager import BaseManager
    from django.http import (
        HttpRequest,
        HttpResponse,
    )
    from httpx import Response
if TYPE_CHECKING:
    from django.http import (
        HttpRequest,
        HttpResponse,
    )
    from httpx import Response

logger: logging.Logger = logging.getLogger(__name__)

cache_dir: Path = settings.DATA_DIR / "cache"
cache_dir.mkdir(exist_ok=True, parents=True)
storage = hishel.FileStorage(base_path=cache_dir)
controller = hishel.Controller(
    cacheable_status_codes=[200, 203, 204, 206, 300, 301, 308, 404, 405, 410, 414, 501],
    allow_stale=True,
    always_revalidate=True,
)


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


def index(request: HttpRequest) -> HttpResponse:
    """Render the index page."""
    orgs: BaseManager[Organization] = Organization.objects.all()
    webhooks: list[WebhookData] = [get_webhook_data(webhook) for webhook in get_webhooks(request)]

    return TemplateResponse(
        request=request,
        template="index.html",
        context={"orgs": orgs, "webhooks": webhooks},
    )
