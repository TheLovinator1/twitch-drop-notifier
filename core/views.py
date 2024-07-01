import logging
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

from core.discord import send
from core.models import DiscordSetting
from twitch_app.models import (
    DropBenefit,
    DropCampaign,
    Game,
    Organization,
    TimeBasedDrop,
)

from .forms import DiscordSettingForm

if TYPE_CHECKING:
    from django.contrib.auth.base_user import AbstractBaseUser
    from django.contrib.auth.models import AnonymousUser
    from django.db.models.manager import BaseManager
from django.views.decorators.http import require_POST

logger: logging.Logger = logging.getLogger(__name__)


def index(request: HttpRequest) -> HttpResponse:
    """/ index page.

    Args:
        request: The request.

    Returns:
        HttpResponse: Returns the index page.
    """
    organizations: BaseManager[Organization] = Organization.objects.all()

    orgs_data = {org: {"games": {}, "drop_campaigns": []} for org in organizations}
    for org in organizations:
        drop_benefits: BaseManager[DropBenefit] = DropBenefit.objects.filter(
            owner_organization=org,
        )
        games: set[Game] = {benefit.game for benefit in drop_benefits}

        for game in games:
            if game not in orgs_data[org]["games"]:
                orgs_data[org]["games"][game] = {
                    "drop_benefits": [],
                    "time_based_drops": [],
                }

        for benefit in drop_benefits:
            orgs_data[org]["games"][benefit.game]["drop_benefits"].append(benefit)

        time_based_drops: BaseManager[TimeBasedDrop] = TimeBasedDrop.objects.filter(
            benefits__in=drop_benefits,
        ).distinct()
        for drop in time_based_drops:
            for benefit in drop.benefits.all():
                if benefit.game in orgs_data[org]["games"]:
                    orgs_data[org]["games"][benefit.game]["time_based_drops"].append(
                        drop,
                    )

        drop_campaigns: BaseManager[DropCampaign] = DropCampaign.objects.filter(
            owner=org,
        )
        for campaign in drop_campaigns:
            orgs_data[org]["drop_campaigns"].append(campaign)

    if request.user.is_authenticated:
        discord_settings: BaseManager[DiscordSetting] = DiscordSetting.objects.filter(
            user=request.user,
        )

    context = {
        "orgs_data": orgs_data,
        "discord_settings": discord_settings if request.user.is_authenticated else None,
    }

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
