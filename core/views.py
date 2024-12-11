from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from django.db.models import F, Prefetch
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.template.response import TemplateResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from core.import_json import import_data_from_view
from core.models import Benefit, DropCampaign, Game, TimeBasedDrop

if TYPE_CHECKING:
    from django.db.models.query import QuerySet
    from django.http import HttpRequest

logger: logging.Logger = logging.getLogger(__name__)


def get_games_with_drops() -> QuerySet[Game]:
    """Get the games with drops, sorted by when the drop campaigns end.

    Returns:
        QuerySet[Game]: The games with drops.
    """
    # Prefetch the benefits for the time-based drops.
    benefits_prefetch = Prefetch(lookup="benefits", queryset=Benefit.objects.all())
    active_time_based_drops: QuerySet[TimeBasedDrop] = TimeBasedDrop.objects.filter(
        ends_at__gte=timezone.now(),
        starts_at__lte=timezone.now(),
    ).prefetch_related(benefits_prefetch)

    # Prefetch the active time-based drops for the drop campaigns.
    drops_prefetch = Prefetch(lookup="drops", queryset=active_time_based_drops)
    active_campaigns: QuerySet[DropCampaign] = DropCampaign.objects.filter(
        ends_at__gte=timezone.now(),
        starts_at__lte=timezone.now(),
    ).prefetch_related(drops_prefetch)

    return (
        Game.objects.filter(drop_campaigns__in=active_campaigns)
        .annotate(drop_campaign_end=F("drop_campaigns__ends_at"))
        .distinct()
        .prefetch_related(Prefetch("drop_campaigns", queryset=active_campaigns))
        .select_related("org")
        .order_by("drop_campaign_end")
    )


@require_http_methods(request_method_list=["GET", "HEAD"])
def get_home(request: HttpRequest) -> HttpResponse:
    """Render the index page.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The response object
    """
    try:
        games: QuerySet[Game] = get_games_with_drops()
    except Exception:
        logger.exception("Error fetching reward campaigns or games.")
        return HttpResponse(status=500)

    context: dict[str, Any] = {"games": games}
    return TemplateResponse(request, "index.html", context)


@require_http_methods(request_method_list=["GET", "HEAD"])
def get_game(request: HttpRequest, twitch_id: int) -> HttpResponse:
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
        return HttpResponse(status=404, content="Game not found.")
    except Game.MultipleObjectsReturned:
        return HttpResponse(status=500, content="Multiple games found with the same Twitch ID.")

    context: dict[str, Any] = {"game": game}
    return TemplateResponse(request=request, template="game.html", context=context)


@require_http_methods(request_method_list=["GET", "HEAD"])
def get_games(request: HttpRequest) -> HttpResponse:
    """Render the game view page.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The response object.
    """
    games: QuerySet[Game] = Game.objects.all()

    context: dict[str, QuerySet[Game] | str] = {"games": games}
    return TemplateResponse(request=request, template="games.html", context=context)


@require_http_methods(request_method_list=["POST"])
def get_import(request: HttpRequest) -> HttpResponse:
    """Import data that are sent from Twitch Drop Miner.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The response object.
    """
    try:
        data = json.loads(request.body)
        logger.info(data)

        # Import the data.
        import_data_from_view(data)

        return JsonResponse({"status": "success"}, status=200)
    except json.JSONDecodeError as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)
