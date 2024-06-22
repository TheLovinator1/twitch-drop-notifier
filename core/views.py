from typing import TYPE_CHECKING

from django.http import HttpRequest, HttpResponse
from django.template.response import TemplateResponse

from twitch.models import (
    DropBenefit,
    DropCampaign,
    Game,
    Organization,
    TimeBasedDrop,
)

if TYPE_CHECKING:
    from django.db.models.manager import BaseManager


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

        time_based_drops = TimeBasedDrop.objects.filter(
            benefits__in=drop_benefits,
        ).distinct()
        for drop in time_based_drops:
            for benefit in drop.benefits.all():
                if benefit.game in orgs_data[org]["games"]:
                    orgs_data[org]["games"][benefit.game]["time_based_drops"].append(
                        drop,
                    )

        drop_campaigns = DropCampaign.objects.filter(owner=org)
        for campaign in drop_campaigns:
            orgs_data[org]["drop_campaigns"].append(campaign)

    return TemplateResponse(
        request=request,
        template="index.html",
        context={"orgs_data": orgs_data},
    )
