import datetime
from dataclasses import dataclass


@dataclass
class WebhookData:
    """The webhook data."""

    name: str | None = None
    url: str | None = None
    avatar: str | None = None
    status: str | None = None
    response: str | None = None


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
