import logging
from typing import TYPE_CHECKING

from django.db.models.manager import BaseManager
from django.http import HttpRequest, HttpResponse
from django.template.response import TemplateResponse

from core.discord import send
from twitch.models import (
    DropBenefit,
    DropCampaign,
    Game,
    Organization,
    TimeBasedDrop,
)

if TYPE_CHECKING:
    from django.db.models.manager import BaseManager
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)


def index(request: HttpRequest) -> HttpResponse:
    """/ index page.

    Args:
        request: The request.

    Returns:
        HttpResponse: Returns the index page.
    """
    organizations: BaseManager[Organization] = Organization.objects.all()

    # Organize the data
    orgs_data = {}
    for org in organizations:
        orgs_data[org] = {"games": {}, "drop_campaigns": []}

    # Populate the games under each organization through DropBenefit and DropCampaign
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

    return TemplateResponse(
        request=request,
        template="index.html",
        context={"orgs_data": orgs_data},
    )


@require_POST
def test_webhook(
    request: HttpRequest,
    *args,  # noqa: ANN002, ARG001
    **kwargs,  # noqa: ARG001, ANN003
) -> HttpResponse:
    """Test webhook.

    Args:
        request: The request.
        args: Additional arguments.
        kwargs: Additional keyword arguments.

    Returns:
        HttpResponse: Returns a response.
    """
    org_id: str | None = request.POST.get("org_id")
    if not org_id:
        return HttpResponse(status=400)

    campaign: DropCampaign = DropCampaign.objects.get(id=org_id)

    msg: str = f"""
Found new drop for {campaign.game.display_name}:\n
{campaign.name}\n
{campaign.description}\n
<{campaign.details_url}>
"""
    send(msg.strip())

    return HttpResponse(status=200)
