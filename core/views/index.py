from __future__ import annotations

import datetime
import logging
from typing import TYPE_CHECKING

import hishel
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.template.response import TemplateResponse

from core.data import CampaignContext, DropContext, GameContext, WebhookData
from twitch_app.models import (
    DropBenefit,
    DropCampaign,
    Game,
    TimeBasedDrop,
)

if TYPE_CHECKING:
    from pathlib import Path

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


def fetch_campaigns(game: Game) -> list[CampaignContext]:
    """Fetch active campaigns for a given game."""
    campaigns: list[CampaignContext] = []
    for campaign in DropCampaign.objects.filter(
        game=game,
        status="ACTIVE",
        end_at__gt=datetime.datetime.now(tz=datetime.UTC),
    ).only(
        "id",
        "name",
        "image_url",
        "status",
        "account_link_url",
        "description",
        "details_url",
        "start_at",
        "end_at",
    ):
        drops = fetch_drops(campaign)
        if not drops:
            logger.info("No drops found for %s", campaign.name)
            continue

        campaigns.append(
            CampaignContext(
                drop_id=campaign.id,
                name=campaign.name,
                image_url=campaign.image_url,
                status=campaign.status,
                account_link_url=campaign.account_link_url,
                description=campaign.description,
                details_url=campaign.details_url,
                start_at=campaign.start_at,
                end_at=campaign.end_at,
                drops=drops,
            ),
        )
    return campaigns


def fetch_drops(campaign: DropCampaign) -> list[DropContext]:
    """Fetch drops for a given campaign."""
    drops: list[DropContext] = []
    drop: TimeBasedDrop
    for drop in campaign.time_based_drops.all().only(
        "id",
        "name",
        "required_minutes_watched",
        "required_subs",
    ):
        benefit: DropBenefit | None = drop.benefits.first()

        image_asset_url: str = "https://static-cdn.jtvnw.net/twitch-quests-assets/CAMPAIGN/default.png"
        if benefit and benefit.image_asset_url:
            image_asset_url = benefit.image_asset_url

        drops.append(
            DropContext(
                drops_id=drop.id,
                image_url=image_asset_url,
                name=drop.name,
                required_minutes_watched=drop.required_minutes_watched,
                required_subs=drop.required_subs,
            ),
        )
    return drops


def sort_games_by_campaign_start(list_of_games: list[GameContext]) -> list[GameContext]:
    """Sort games by the start date of the first campaign and reverse the list so the latest games are first."""
    if list_of_games and list_of_games[0].campaigns:
        list_of_games.sort(
            key=lambda x: x.campaigns[0].start_at
            if x.campaigns and x.campaigns[0].start_at is not None
            else datetime.datetime.min,
        )
    list_of_games.reverse()
    return list_of_games


def get_webhooks(request: HttpRequest) -> list[str]:
    """Get the webhooks from the cookie."""
    cookie: str = request.COOKIES.get("webhooks", "")
    return list(filter(None, cookie.split(",")))


def prepare_game_contexts() -> list[GameContext]:
    """Prepare game contexts with their respective campaigns and drops."""
    list_of_games: list[GameContext] = []
    for game in list(Game.objects.all().only("id", "image_url", "display_name", "slug")):
        campaigns: list[CampaignContext] = fetch_campaigns(game)
        if not campaigns:
            continue
        list_of_games.append(
            GameContext(
                game_id=game.id,
                campaigns=campaigns,
                image_url=game.image_url,
                display_name=game.display_name,
                twitch_url=game.twitch_url,
            ),
        )
    return list_of_games


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
    list_of_games: list[GameContext] = prepare_game_contexts()
    sorted_list_of_games: list[GameContext] = sort_games_by_campaign_start(list_of_games)
    webhooks: list[WebhookData] = [get_webhook_data(webhook) for webhook in get_webhooks(request)]

    return TemplateResponse(
        request=request,
        template="index.html",
        context={"games": sorted_list_of_games, "webhooks": webhooks},
    )
