from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.db.models.manager import BaseManager
from django.template.response import TemplateResponse

from core.models import Game, RewardCampaign

if TYPE_CHECKING:
    from django.db.models.manager import BaseManager
    from django.http import HttpRequest, HttpResponse

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
    reward_campaigns: BaseManager[RewardCampaign] = RewardCampaign.objects.all()

    toc: str = build_toc([
        TOCItem(name="Information", toc_id="#info-box"),
        TOCItem(name="Games", toc_id="#games"),
    ])

    context: dict[str, BaseManager[RewardCampaign] | str] = {"reward_campaigns": reward_campaigns, "toc": toc}
    return TemplateResponse(request=request, template="index.html", context=context)


def game_view(request: HttpRequest) -> HttpResponse:
    """Render the game view page.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The response object.
    """
    games: BaseManager[Game] = Game.objects.all()

    tocs: list[TOCItem] = [
        TOCItem(name=game.display_name, toc_id=game.slug) for game in games if game.display_name and game.slug
    ]
    toc: str = build_toc(tocs)

    context: dict[str, BaseManager[Game] | str] = {"games": games, "toc": toc}
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
