from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import requests_cache
from django.db.models import Prefetch
from django.db.models.manager import BaseManager
from django.http import HttpRequest, HttpResponse
from django.template.response import TemplateResponse
from django.utils import timezone
from django.views import View

from core.models import Benefit, DropCampaign, Game, RewardCampaign, TimeBasedDrop, Webhook

if TYPE_CHECKING:
    from django.db.models.manager import BaseManager
    from django.http import HttpRequest

logger: logging.Logger = logging.getLogger(__name__)


def get_reward_campaigns() -> BaseManager[RewardCampaign]:
    """Get the reward campaigns.

    Returns:
        BaseManager[RewardCampaign]: The reward campaigns.
    """
    return RewardCampaign.objects.all().prefetch_related("rewards").order_by("-created_at")


def get_games_with_drops() -> BaseManager[Game]:
    """Get the games with drops.

    Returns:
        BaseManager[Game]: The games with drops.
    """
    # Prefetch the benefits for the active drops.
    # Benefits have more information about the drop. Used for getting image_url.
    benefits: BaseManager[Benefit] = Benefit.objects.all()
    benefits_prefetch = Prefetch(lookup="benefits", queryset=benefits)
    active_time_based_drops: BaseManager[TimeBasedDrop] = TimeBasedDrop.objects.filter(
        ends_at__gte=timezone.now(),
    ).prefetch_related(benefits_prefetch)

    # Prefetch the drops for the active campaigns.
    active_campaigns: BaseManager[DropCampaign] = DropCampaign.objects.filter(ends_at__gte=timezone.now())
    drops_prefetch = Prefetch(lookup="drops", queryset=active_time_based_drops)
    campaigns_prefetch = Prefetch(
        lookup="drop_campaigns",
        queryset=active_campaigns.prefetch_related(drops_prefetch),
    )

    return (
        Game.objects.filter(drop_campaigns__in=active_campaigns)
        .distinct()
        .prefetch_related(campaigns_prefetch)
        .order_by("name")
    )


def index(request: HttpRequest) -> HttpResponse:
    """Render the index page.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The response object
    """
    try:
        reward_campaigns: BaseManager[RewardCampaign] = get_reward_campaigns()
        games: BaseManager[Game] = get_games_with_drops()

    except Exception:
        logger.exception("Error fetching reward campaigns or games.")
        return HttpResponse(status=500)

    context: dict[str, Any] = {
        "reward_campaigns": reward_campaigns,
        "games": games,
    }
    return TemplateResponse(request, "index.html", context)


def game_view(request: HttpRequest, twitch_id: int) -> HttpResponse:
    """Render the game view page.

    Args:
        request (HttpRequest): The request object.
        twitch_id (int): The Twitch ID of the game.

    Returns:
        HttpResponse: The response object.
    """
    try:
        time_based_drops_prefetch = Prefetch(
            lookup="drops",
            queryset=TimeBasedDrop.objects.prefetch_related("benefits"),
        )
        drop_campaigns_prefetch = Prefetch(
            lookup="drop_campaigns",
            queryset=DropCampaign.objects.prefetch_related(time_based_drops_prefetch),
        )
        game: Game = (
            Game.objects.select_related("org").prefetch_related(drop_campaigns_prefetch).get(twitch_id=twitch_id)
        )

    except Game.DoesNotExist:
        return HttpResponse(status=404)
    except Game.MultipleObjectsReturned:
        return HttpResponse(status=500)

    context: dict[str, Any] = {"game": game}
    return TemplateResponse(request=request, template="game.html", context=context)


def games_view(request: HttpRequest) -> HttpResponse:
    """Render the game view page.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The response object.
    """
    games: BaseManager[Game] = Game.objects.all()

    context: dict[str, BaseManager[Game] | str] = {"games": games}
    return TemplateResponse(request=request, template="games.html", context=context)


def reward_campaign_view(request: HttpRequest) -> HttpResponse:
    """Render the reward campaign view page.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The response object.
    """
    reward_campaigns: BaseManager[RewardCampaign] = RewardCampaign.objects.all()
    context: dict[str, BaseManager[RewardCampaign]] = {"reward_campaigns": reward_campaigns}
    return TemplateResponse(request=request, template="reward_campaigns.html", context=context)


def get_webhook_data(webhook_url: str) -> dict[str, str]:
    """Get the webhook data from the URL.

    Args:
        webhook_url (str): The webhook URL.

    Returns:
        dict[str, str]: The webhook data.
    """
    session = requests_cache.CachedSession("webhook_cache")
    response: requests_cache.OriginalResponse | requests_cache.CachedResponse = session.get(webhook_url)
    return response.json()


def split_webhook_url(webhook_url: str) -> tuple[str, str]:
    """Split the webhook URL into its components.

    Webhooks are in the format:
        https://discord.com/api/webhooks/{id}/{token}

    Args:
        webhook_url (str): The webhook URL.

    Returns:
        tuple[str, str]: The ID and token.
    """
    webhook_id: str = webhook_url.split("/")[-2]
    webhook_token: str = webhook_url.split("/")[-1]
    return webhook_id, webhook_token


class WebhooksView(View):
    """Render the webhook view page."""

    @staticmethod
    def post(request: HttpRequest) -> HttpResponse:
        """Add a webhook to the list of webhooks.

        Args:
            request (HttpRequest): The request object.

        Returns:
            HttpResponse: The response object.
        """
        webhook_url: str | None = request.POST.get("webhook_url")
        if not webhook_url:
            return HttpResponse(content="No webhook URL provided.", status=400)

        # Read webhooks from cookie.
        webhooks_cookies: str | None = request.COOKIES.get("webhooks")
        webhooks_list: list[str] = webhooks_cookies.split(",") if webhooks_cookies else []

        # Get webhook data.
        webhook_id, webhook_token = split_webhook_url(webhook_url)
        webhook_data: dict[str, str] = get_webhook_data(webhook_url)
        list_of_json_keys: list[str] = ["avatar", "channel_id", "guild_id", "name", "type", "url"]
        defaults: dict[str, str | None] = {key: webhook_data.get(key) for key in list_of_json_keys}

        # Warn if JSON has more keys than expected.
        if len(webhook_data.keys()) > len(list_of_json_keys):
            logger.warning("Unexpected keys in JSON: %s", webhook_data.keys())

        # Add the webhook to the database.
        new_webhook, created = Webhook.objects.update_or_create(
            id=webhook_id,
            token=webhook_token,
            defaults=defaults,
        )
        if created:
            logger.info("Created webhook '%s'.", new_webhook)

        # Add the new webhook to the list.
        webhooks_list.append(webhook_url)

        # Remove duplicates.
        webhooks_list = list(set(webhooks_list))

        # Save the new list of webhooks to the cookie.
        response: HttpResponse = HttpResponse()
        response.set_cookie("webhooks", ",".join(webhooks_list))

        # Redirect to the webhooks page.
        response["Location"] = "/webhooks/"
        response.status_code = 302
        return response

    @staticmethod
    def get(request: HttpRequest) -> HttpResponse:
        # Read webhooks from cookie.
        webhooks_cookies: str | None = request.COOKIES.get("webhooks")
        webhooks_list: list[str] = webhooks_cookies.split(",") if webhooks_cookies else []

        webhooks_from_db: list[Webhook] = []
        # Get the webhooks from the database.
        for webhook_url in webhooks_list:
            webhook_id, webhook_token = split_webhook_url(webhook_url)

            # Check if the webhook is in the database.
            if not Webhook.objects.filter(id=webhook_id, token=webhook_token).exists():
                webhook_data: dict[str, str] = get_webhook_data(webhook_url)
                list_of_json_keys: list[str] = ["avatar", "channel_id", "guild_id", "name", "type", "url"]
                defaults: dict[str, str | None] = {key: webhook_data.get(key) for key in list_of_json_keys}

                # Warn if JSON has more keys than expected.
                if len(webhook_data.keys()) > len(list_of_json_keys):
                    logger.warning("Unexpected keys in JSON: %s", webhook_data.keys())

                new_webhook, created = Webhook.objects.update_or_create(
                    id=webhook_id,
                    token=webhook_token,
                    defaults=defaults,
                )
                if created:
                    logger.info("Created webhook '%s'.", new_webhook)

                webhooks_from_db.append(new_webhook)

            # If the webhook is in the database, get it from there.
            else:
                existing_webhook: Webhook = Webhook.objects.get(id=webhook_id, token=webhook_token)
                webhooks_from_db.append(existing_webhook)

        context: dict[str, list[Webhook]] = {"webhooks": webhooks_from_db}
        return TemplateResponse(request=request, template="webhooks.html", context=context)
