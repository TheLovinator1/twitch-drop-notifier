import datetime
import logging
from dataclasses import dataclass

import httpx
from django.contrib import messages
from django.http import (
    HttpRequest,
    HttpResponse,
)
from django.template.response import TemplateResponse
from django.views.decorators.http import require_POST
from django.views.generic import ListView, TemplateView

from twitch_app.models import (
    DropBenefit,
    DropCampaign,
    Game,
    TimeBasedDrop,
)

from .forms import DiscordSettingForm

logger: logging.Logger = logging.getLogger(__name__)


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
    status: str | None = None
    response: str | None = None


class Webhooks(TemplateView):
    model = Game
    template_name: str = "webhooks.html"
    context_object_name: str = "webhooks"
    paginate_by = 100

    def get_context_data(self, **kwargs) -> dict[str, list[WebhookData] | DiscordSettingForm]:  # noqa: ANN003, ARG002
        """Get the context data for the view."""
        cookie: str = self.request.COOKIES.get("webhooks", "")
        webhooks: list[str] = cookie.split(",")
        webhooks = list(filter(None, webhooks))

        webhook_respones: list[WebhookData] = []

        # Use httpx to connect to webhook url and get the response
        # Use the response to get name of the webhook
        with httpx.Client() as client:
            for webhook in webhooks:
                our_webhook = WebhookData(name="Unknown", url=webhook, status="Failed", response="No response")
                response: httpx.Response = client.get(url=webhook)
                if response.is_success:
                    our_webhook.name = response.json()["name"]
                    our_webhook.status = "Success"
                    our_webhook.response = response.text
                else:
                    our_webhook.status = "Failed"
                    our_webhook.response = response.text

                # Add to the list of webhooks
                webhook_respones.append(our_webhook)

        return {"webhooks": webhook_respones, "form": DiscordSettingForm()}


@require_POST
def add_webhook(request: HttpRequest) -> HttpResponse:
    """Add a webhook to the list of webhooks."""
    form = DiscordSettingForm(request.POST)

    if form.is_valid():
        webhook = str(form.cleaned_data["webhook"])
        response = HttpResponse()

        if "webhooks" in request.COOKIES:
            cookie: str = request.COOKIES["webhooks"]
            webhooks: list[str] = cookie.split(",")
            webhooks = list(filter(None, webhooks))
            if webhook in webhooks:
                messages.error(request, "Webhook already exists.")
                return response
            webhooks.append(webhook)
            webhook: str = ",".join(webhooks)

        response.set_cookie(key="webhooks", value=webhook, max_age=60 * 60 * 24 * 365)

        messages.info(request, "Webhook successfully added.")
        return response

    return HttpResponse(status=400, content="Invalid form data.")
