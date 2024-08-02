from datetime import datetime
from enum import Enum
from uuid import UUID


class SelfTypename(Enum):
    DROP_CAMPAIGN_SELF_EDGE = "DropCampaignSelfEdge"


class Self:
    is_account_connected: bool
    typename: SelfTypename

    def __init__(self, is_account_connected: bool, typename: SelfTypename) -> None:
        self.is_account_connected = is_account_connected
        self.typename = typename


class GameTypename(Enum):
    GAME = "Game"


class Game:
    id: int
    display_name: str
    box_art_url: str
    typename: GameTypename

    def __init__(self, id: int, display_name: str, box_art_url: str, typename: GameTypename) -> None:
        self.id = id
        self.display_name = display_name
        self.box_art_url = box_art_url
        self.typename = typename


class OwnerTypename(Enum):
    ORGANIZATION = "Organization"


class Owner:
    id: UUID
    name: str
    typename: OwnerTypename

    def __init__(self, id: UUID, name: str, typename: OwnerTypename) -> None:
        self.id = id
        self.name = name
        self.typename = typename


class Status(Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"


class DropCampaignTypename(Enum):
    DROP_CAMPAIGN = "DropCampaign"


class DropCampaign:
    id: UUID
    name: str
    owner: Owner
    game: Game
    status: Status
    start_at: datetime
    end_at: datetime
    details_url: str
    account_link_url: str
    drop_campaign_self: Self
    typename: DropCampaignTypename

    def __init__(
        self,
        id: UUID,
        name: str,
        owner: Owner,
        game: Game,
        status: Status,
        start_at: datetime,
        end_at: datetime,
        details_url: str,
        account_link_url: str,
        drop_campaign_self: Self,
        typename: DropCampaignTypename,
    ) -> None:
        self.id = id
        self.name = name
        self.owner = owner
        self.game = game
        self.status = status
        self.start_at = start_at
        self.end_at = end_at
        self.details_url = details_url
        self.account_link_url = account_link_url
        self.drop_campaign_self = drop_campaign_self
        self.typename = typename


class CurrentUser:
    id: int
    login: str
    drop_campaigns: list[DropCampaign]
    typename: str

    def __init__(self, id: int, login: str, drop_campaigns: list[DropCampaign], typename: str) -> None:
        self.id = id
        self.login = login
        self.drop_campaigns = drop_campaigns
        self.typename = typename


class Image:
    image1_x_url: str
    typename: str

    def __init__(self, image1_x_url: str, typename: str) -> None:
        self.image1_x_url = image1_x_url
        self.typename = typename


class Reward:
    id: UUID
    name: str
    banner_image: Image
    thumbnail_image: Image
    earnable_until: datetime
    redemption_instructions: str
    redemption_url: str
    typename: str

    def __init__(
        self,
        id: UUID,
        name: str,
        banner_image: Image,
        thumbnail_image: Image,
        earnable_until: datetime,
        redemption_instructions: str,
        redemption_url: str,
        typename: str,
    ) -> None:
        self.id = id
        self.name = name
        self.banner_image = banner_image
        self.thumbnail_image = thumbnail_image
        self.earnable_until = earnable_until
        self.redemption_instructions = redemption_instructions
        self.redemption_url = redemption_url
        self.typename = typename


class UnlockRequirements:
    subs_goal: int
    minute_watched_goal: int
    typename: str

    def __init__(self, subs_goal: int, minute_watched_goal: int, typename: str) -> None:
        self.subs_goal = subs_goal
        self.minute_watched_goal = minute_watched_goal
        self.typename = typename


class RewardCampaignsAvailableToUser:
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
    game: None
    unlock_requirements: UnlockRequirements
    image: Image
    rewards: list[Reward]
    typename: str

    def __init__(
        self,
        id: UUID,
        name: str,
        brand: str,
        starts_at: datetime,
        ends_at: datetime,
        status: str,
        summary: str,
        instructions: str,
        external_url: str,
        reward_value_url_param: str,
        about_url: str,
        is_sitewide: bool,
        game: None,
        unlock_requirements: UnlockRequirements,
        image: Image,
        rewards: list[Reward],
        typename: str,
    ) -> None:
        self.id = id
        self.name = name
        self.brand = brand
        self.starts_at = starts_at
        self.ends_at = ends_at
        self.status = status
        self.summary = summary
        self.instructions = instructions
        self.external_url = external_url
        self.reward_value_url_param = reward_value_url_param
        self.about_url = about_url
        self.is_sitewide = is_sitewide
        self.game = game
        self.unlock_requirements = unlock_requirements
        self.image = image
        self.rewards = rewards
        self.typename = typename


class Data:
    current_user: CurrentUser
    reward_campaigns_available_to_user: list[RewardCampaignsAvailableToUser]

    def __init__(
        self,
        current_user: CurrentUser,
        reward_campaigns_available_to_user: list[RewardCampaignsAvailableToUser],
    ) -> None:
        self.current_user = current_user
        self.reward_campaigns_available_to_user = reward_campaigns_available_to_user


class Extensions:
    duration_milliseconds: int
    operation_name: str
    request_id: str

    def __init__(self, duration_milliseconds: int, operation_name: str, request_id: str) -> None:
        self.duration_milliseconds = duration_milliseconds
        self.operation_name = operation_name
        self.request_id = request_id


class RewardCampaign11:
    data: Data
    extensions: Extensions

    def __init__(self, data: Data, extensions: Extensions) -> None:
        self.data = data
        self.extensions = extensions
