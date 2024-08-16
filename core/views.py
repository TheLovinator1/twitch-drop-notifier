from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

import requests_cache
from django.db.models import Prefetch
from django.db.models.manager import BaseManager
from django.http import HttpRequest, HttpResponse
from django.template.response import TemplateResponse
from django.utils import timezone
from django.views import View

from core.models import DropCampaign, Game, RewardCampaign, Webhook

if TYPE_CHECKING:
    from django.db.models.manager import BaseManager
    from django.http import HttpRequest

logger: logging.Logger = logging.getLogger(__name__)


@dataclass
class TOCItem:
    """Table of contents item."""

    name: str
    toc_id: str


def build_toc(list_of_things: list[TOCItem]) -> str:
    """Build the table of contents.

    Args:
        list_of_things (list[TOCItem]): The list of table of contents items.

    Returns:
        str: The HTML for the table of contents.
    """
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
    """Render the index page.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The response object
    """
    reward_campaigns: BaseManager[RewardCampaign] = (
        RewardCampaign.objects.all()
        .prefetch_related("rewards")
        .filter(ends_at__gt=timezone.now(), starts_at__lt=timezone.now())
    )
    future_campaigns: BaseManager[DropCampaign] = DropCampaign.objects.filter(
        ends_at__gt=timezone.now(),
        starts_at__lt=timezone.now(),
    )

    games: BaseManager[Game] = Game.objects.all().prefetch_related(
        Prefetch("drop_campaigns", queryset=future_campaigns.prefetch_related("drops__benefits")),
    )
    tocs: list[TOCItem] = []
    for game in games.all():
        game_name: str = game.name or "<div class='text-muted'>Game name unknown</div>"
        tocs.append(TOCItem(name=game_name, toc_id=f"#{game.twitch_id}"))

    toc: str = build_toc(tocs)

    context: dict[str, BaseManager[RewardCampaign] | str | BaseManager[Game]] = {
        "reward_campaigns": reward_campaigns,
        "games": games,
        "toc": toc,
    }
    return TemplateResponse(request=request, template="index.html", context=context)


def game_view(request: HttpRequest) -> HttpResponse:
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
