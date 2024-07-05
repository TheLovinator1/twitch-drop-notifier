from __future__ import annotations

import datetime
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import hishel
from django.conf import settings
from django.contrib import messages
from django.http.response import HttpResponse
from django.template.response import TemplateResponse
from django.views.generic import FormView, ListView
from httpx._models import Response

from twitch_app.models import (
    DropBenefit,
    DropCampaign,
    Game,
    TimeBasedDrop,
)

from .forms import DiscordSettingForm

if TYPE_CHECKING:
    from pathlib import Path

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


@dataclass
class DropContext:
    """The drop."""

    drops_id: str | None = None
    image_url: str | None = None
    name: str | None = None
    limit: int | None = None
    required_minutes_watched: int | None = None
    required_subs: int | None = None


@dataclass
class CampaignContext:
    """Drops are grouped into campaigns."""

    drop_id: str | None = None
    name: str | None = None
    image_url: str | None = None
    status: str | None = None
    account_link_url: str | None = None
    description: str | None = None
    details_url: str | None = None
    ios_available: bool | None = None
    start_at: datetime.datetime | None = None
    end_at: datetime.datetime | None = None
    drops: list[DropContext] | None = None


@dataclass
class GameContext:
    """Campaigns are under a game."""

    game_id: str | None = None
    campaigns: list[CampaignContext] | None = None
    image_url: str | None = None
    display_name: str | None = None
    twitch_url: str | None = None
    slug: str | None = None


def fetch_games() -> list[Game]:
    """Fetch all games with necessary fields."""
    return list(Game.objects.all().only("id", "image_url", "display_name", "slug"))


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


def prepare_game_contexts() -> list[GameContext]:
    """Prepare game contexts with their respective campaigns and drops."""
    list_of_games: list[GameContext] = []
    for game in fetch_games():
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


def index(request: HttpRequest) -> HttpResponse:
    """Render the index page."""
    list_of_games: list[GameContext] = prepare_game_contexts()
    sorted_list_of_games: list[GameContext] = sort_games_by_campaign_start(list_of_games)

    return TemplateResponse(
        request=request,
        template="index.html",
        context={"games": sorted_list_of_games},
    )


class GameView(ListView):
    model = Game
    template_name: str = "games.html"
    context_object_name: str = "games"
    paginate_by = 100


@dataclass
class WebhookData:
    """The webhook data."""

    name: str | None = None
    url: str | None = None
    avatar: str | None = None
    status: str | None = None
    response: str | None = None


class WebhooksView(FormView):
    model = Game
    template_name = "webhooks.html"
    form_class = DiscordSettingForm
    context_object_name: str = "webhooks"
    paginate_by = 100

    def get_context_data(self: WebhooksView, **kwargs: dict[str, WebhooksView] | DiscordSettingForm) -> dict[str, Any]:
        """Get the context data for the view."""
        context: dict[str, DiscordSettingForm | list[WebhookData]] = super().get_context_data(**kwargs)
        cookie: str = self.request.COOKIES.get("webhooks", "")
        webhooks: list[str] = cookie.split(",")
        webhooks = list(filter(None, webhooks))

        webhook_responses: list[WebhookData] = []

        with hishel.CacheClient(storage=storage, controller=controller) as client:
            for webhook in webhooks:
                our_webhook = WebhookData(name="Unknown", url=webhook, status="Failed", response="No response")
                response: Response = client.get(url=webhook, extensions={"cache_metadata": True})
                if response.is_success:
                    our_webhook.name = response.json().get("name", "Unknown")
                    our_webhook.status = "Success"
                else:
                    our_webhook.status = "Failed"

                our_webhook.response = response.text

                if response.json().get("id") and response.json().get("avatar"):
                    avatar_url: str = f'https://cdn.discordapp.com/avatars/{response.json().get("id")}/{response.json().get("avatar")}.png'

                our_webhook.avatar = avatar_url or "https://cdn.discordapp.com/embed/avatars/0.png"

                webhook_responses.append(our_webhook)

        context.update({
            "webhooks": webhook_responses,
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
        response.set_cookie(key="webhooks", value=",".join(webhooks), max_age=60 * 60 * 24 * 365)

        messages.success(self.request, "Webhook successfully added.")
        return response

    def form_invalid(self: WebhooksView, form: DiscordSettingForm) -> HttpResponse:
        messages.error(self.request, "Failed to add webhook.")
        return self.render_to_response(self.get_context_data(form=form))
