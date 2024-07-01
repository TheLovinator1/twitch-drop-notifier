import datetime

from django.db.models.manager import BaseManager
from django.http import HttpRequest
from ninja import Router, Schema

from .models import (
    DropBenefit,
    DropCampaign,
    Game,
    Organization,
    TimeBasedDrop,
)

router = Router(
    tags=["twitch"],
)


class OrganizationSchema(Schema):
    id: str | None = None
    name: str | None = None
    added_at: datetime.datetime | None = None
    modified_at: datetime.datetime | None = None


class ChannelSchema(Schema):
    id: str
    display_name: str | None = None
    name: str | None = None
    added_at: datetime.datetime | None = None
    modified_at: datetime.datetime | None = None


class GameSchema(Schema):
    id: str
    slug: str | None = None
    twitch_url: str | None = None
    display_name: str | None = None
    added_at: datetime.datetime | None = None
    modified_at: datetime.datetime | None = None


class DropBenefitSchema(Schema):
    id: str
    created_at: datetime.datetime | None = None
    entitlement_limit: int | None = None
    image_asset_url: str | None = None
    is_ios_available: bool | None = None
    name: str | None = None
    owner_organization: OrganizationSchema
    game: GameSchema
    added_at: datetime.datetime | None = None
    modified_at: datetime.datetime | None = None


class TimeBasedDropSchema(Schema):
    id: str
    required_subs: int | None = None
    end_at: datetime.datetime | None = None
    name: str | None = None
    required_minutes_watched: int | None = None
    start_at: datetime.datetime | None = None
    benefits: list[DropBenefitSchema]
    added_at: datetime.datetime | None = None
    modified_at: datetime.datetime | None = None


class DropCampaignSchema(Schema):
    id: str
    account_link_url: str | None = None
    description: str | None = None
    details_url: str | None = None
    end_at: datetime.datetime | None = None
    image_url: str | None = None
    name: str | None = None
    start_at: datetime.datetime | None = None
    status: str | None = None
    game: GameSchema | None = None
    owner: OrganizationSchema | None = None
    channels: list[ChannelSchema] | None = None
    time_based_drops: list[TimeBasedDropSchema] | None = None
    added_at: datetime.datetime | None = None
    modified_at: datetime.datetime | None = None


# http://localhost:8000/api/twitch/organizations
@router.get("/organizations", response=list[OrganizationSchema])
def get_organizations(
    request: HttpRequest,  # noqa: ARG001
) -> BaseManager[Organization]:
    """Get all organizations."""
    return Organization.objects.all()


# http://localhost:8000/api/twitch/games
@router.get("/games", response=list[GameSchema])
def get_games(request: HttpRequest) -> BaseManager[Game]:  # noqa: ARG001
    """Get all games."""
    return Game.objects.all()


# http://localhost:8000/api/twitch/drop_benefits
@router.get("/drop_benefits", response=list[DropBenefitSchema])
def get_drop_benefits(request: HttpRequest) -> BaseManager[DropBenefit]:  # noqa: ARG001
    """Get all drop benefits."""
    return DropBenefit.objects.all()


# http://localhost:8000/api/twitch/drop_campaigns
@router.get("/drop_campaigns", response=list[DropCampaignSchema])
def get_drop_campaigns(
    request: HttpRequest,  # noqa: ARG001
) -> BaseManager[DropCampaign]:
    """Get all drop campaigns."""
    return DropCampaign.objects.all()


# http://localhost:8000/api/twitch/time_based_drops
@router.get("/time_based_drops", response=list[TimeBasedDropSchema])
def get_time_based_drops(
    request: HttpRequest,  # noqa: ARG001
) -> BaseManager[TimeBasedDrop]:
    """Get all time-based drops."""
    return TimeBasedDrop.objects.all()
