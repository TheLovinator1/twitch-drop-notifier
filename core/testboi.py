from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Game:
    id: int
    slug: str
    display_name: str
    typename: str


@dataclass
class Image:
    image1_x_url: str
    typename: str


@dataclass
class Reward:
    id: UUID
    name: str
    banner_image: Image
    thumbnail_image: Image
    earnable_until: datetime
    redemption_instructions: str
    redemption_url: str
    typename: str


@dataclass
class UnlockRequirements:
    subs_goal: int
    minute_watched_goal: int
    typename: str


@dataclass
class RewardCampaign:
    id: UUID
    name: str
    brand: str
    starts_at: datetime
    ends_at: datetime
    status: str
    summary: str
    instructions: str
    external_url: str
    reward_value_url_param: str
    about_url: str
    is_sitewide: bool
    game: Game
    unlock_requirements: UnlockRequirements
    image: Image
    rewards: list[Reward]
    typename: str
