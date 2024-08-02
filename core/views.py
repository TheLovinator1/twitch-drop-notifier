from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

import hishel
from django.conf import settings
from django.db.models.manager import BaseManager
from django.template.response import TemplateResponse

from core.data import WebhookData
from twitch_app.models import Game, RewardCampaign

if TYPE_CHECKING:
    from pathlib import Path

    from django.db.models.manager import BaseManager
    from django.http import HttpRequest, HttpResponse
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


@dataclass
class TOCItem:
    """Table of contents item."""

    name: str
    toc_id: str


def build_toc(list_of_things: list[TOCItem]) -> str:
    """Build the table of contents."""
    html: str = """
    <div class="position-sticky d-none d-lg-block toc">
        <div class="card">
            <div class="card-body">
                <div id="toc-list" class="list-group">
    """

    for item in list_of_things:
        html += (
            f'<a class="list-group-item list-group-item-action plain-text-item" href="#{item.toc_id}">{item.name}</a>'
        )
    html += """</div></div></div></div>"""
    return html


def index(request: HttpRequest) -> HttpResponse:
    """Render the index page."""
    reward_campaigns: BaseManager[RewardCampaign] = RewardCampaign.objects.all()

    toc: str = build_toc([
        TOCItem(name="Information", toc_id="#info-box"),
        TOCItem(name="Games", toc_id="#games"),
    ])

    context: dict[str, BaseManager[RewardCampaign] | str] = {"reward_campaigns": reward_campaigns, "toc": toc}
    return TemplateResponse(request=request, template="index.html", context=context)


def game_view(request: HttpRequest) -> HttpResponse:
    """Render the game view page."""
    games: BaseManager[Game] = Game.objects.all()

    tocs: list[TOCItem] = [
        TOCItem(name=game.display_name, toc_id=game.slug) for game in games if game.display_name and game.slug
    ]
    toc: str = build_toc(tocs)

    context: dict[str, BaseManager[Game] | str] = {"games": games, "toc": toc}
    return TemplateResponse(request=request, template="games.html", context=context)


def reward_campaign_view(request: HttpRequest) -> HttpResponse:
    """Render the reward campaign view page."""
    reward_campaigns: BaseManager[RewardCampaign] = RewardCampaign.objects.all()
    context: dict[str, BaseManager[RewardCampaign]] = {"reward_campaigns": reward_campaigns}
    return TemplateResponse(request=request, template="reward_campaigns.html", context=context)
