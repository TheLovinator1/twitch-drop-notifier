import datetime
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models.manager import BaseManager
from django.http import (
    HttpRequest,
    HttpResponse,
)
from django.shortcuts import redirect, render
from django.template.response import TemplateResponse
from django.views.generic import ListView

from core.discord import send
from core.models import DiscordSetting
from twitch_app.models import (
    DropBenefit,
    DropCampaign,
    Game,
    TimeBasedDrop,
)

from .forms import DiscordSettingForm

if TYPE_CHECKING:
    from django.contrib.auth.base_user import AbstractBaseUser
    from django.contrib.auth.models import AnonymousUser
    from django.db.models.manager import BaseManager
from django.views.decorators.http import require_POST

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


def index(request: HttpRequest) -> HttpResponse:
    """/ index page.

    Args:
        request: The request.

    Returns:
        HttpResponse: Returns the index page.
    """
    list_of_games: list[GameContext] = []

    for game in Game.objects.all().only("id", "image_url", "display_name", "slug"):
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
            drops: list[DropContext] = []
            drop: TimeBasedDrop
            for drop in campaign.time_based_drops.all().only(
                "id",
                "name",
                "required_minutes_watched",
                "required_subs",
            ):
                benefit: DropBenefit | None = drop.benefits.first()
                image_asset_url: str = (
                    benefit.image_asset_url
                    if benefit
                    else "https://static-cdn.jtvnw.net/twitch-quests-assets/CAMPAIGN/default.png"
                )
                drops.append(
                    DropContext(
                        drops_id=drop.id,
                        image_url=image_asset_url,
                        name=drop.name,
                        required_minutes_watched=drop.required_minutes_watched,
                        required_subs=drop.required_subs,
                    ),
                )

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

        if not campaigns:
            logger.info("No campaigns found for %s", game.display_name)
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

    context: dict[str, list[GameContext]] = {"games": list_of_games}

    return TemplateResponse(
        request=request,
        template="index.html",
        context=context,
    )


@require_POST
def test_webhook(request: HttpRequest) -> HttpResponse:
    """Test webhook.

    Args:
        request: The request.

    Returns:
        HttpResponse: Returns a response.
    """
    org_id: str | None = request.POST.get("org_id")
    if not org_id:
        return HttpResponse(status=400)

    campaign: DropCampaign = DropCampaign.objects.get(id=org_id)

    msg: str = f"Found new drop for {campaign.game.display_name}:\n{campaign.name}\n{campaign.description}"
    send(msg.strip())

    return HttpResponse(status=200)


@login_required
def add_discord_webhook(request: HttpRequest) -> HttpResponse:
    """Add Discord webhook."""
    if request.method == "POST":
        form = DiscordSettingForm(request.POST)
        if form.is_valid():
            DiscordSetting.objects.create(
                user=request.user,
                name=form.cleaned_data["name"],
                webhook_url=form.cleaned_data["webhook_url"],
                disabled=False,
            )

            messages.success(
                request=request,
                message=f"Webhook '{form.cleaned_data["name"]}' added ({form.cleaned_data["webhook_url"]})",
            )

            return redirect("core:add_discord_webhook")
    else:
        form = DiscordSettingForm()

    webhooks: BaseManager[DiscordSetting] = DiscordSetting.objects.filter(
        user=request.user,
    )

    return render(
        request,
        "add_discord_webhook.html",
        {"form": form, "webhooks": webhooks},
    )


@login_required
def delete_discord_webhook(request: HttpRequest) -> HttpResponse:
    """Delete Discord webhook."""
    if request.method == "POST":
        DiscordSetting.objects.filter(
            id=request.POST.get("webhook_id"),
            name=request.POST.get("webhook_name"),
            webhook_url=request.POST.get("webhook_url"),
            user=request.user,
        ).delete()
        messages.success(
            request=request,
            message=f"Webhook '{request.POST.get("webhook_name")}' deleted ({request.POST.get("webhook_url")})",
        )

    return redirect("core:add_discord_webhook")


@login_required
def subscription_create(request: HttpRequest) -> HttpResponse:
    """Create subscription."""
    if request.method == "POST":
        game: Game = Game.objects.get(id=request.POST.get("game_id"))
        user: AbstractBaseUser | AnonymousUser = request.user
        webhook_id: str | None = request.POST.get("webhook_id")
        if not webhook_id:
            messages.error(request, "No webhook ID provided.")
            return redirect("core:index")

        if not user.is_authenticated:
            messages.error(
                request,
                "You need to be logged in to create a subscription.",
            )
            return redirect("core:index")

        logger.info(
            "Current webhooks: %s",
            DiscordSetting.objects.filter(user=user).values_list("id", flat=True),
        )
        discord_webhook: DiscordSetting = DiscordSetting.objects.get(
            id=int(webhook_id),
            user=user,
        )

        messages.success(request, "Subscription created")

        send(
            message=f"This channel will now receive a notification when a new Twitch drop for **{game}** is available.",  # noqa: E501
            webhook_url=discord_webhook.webhook_url,
        )

        return redirect("core:index")

    messages.error(request, "Failed to create subscription")
    return redirect("core:index")


class GameView(ListView):
    model = Game
    template_name: str = "games.html"
    context_object_name: str = "games"
    paginate_by = 100
