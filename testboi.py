from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID


class ChannelTypename(Enum):
    CHANNEL = "Channel"
    GAME = "Game"
    ORGANIZATION = "Organization"


class Channel:
    id: int
    display_name: str
    name: str
    typename: ChannelTypename

    def __init__(self, id: int, display_name: str, name: str, typename: ChannelTypename) -> None:
        self.id = id
        self.display_name = display_name
        self.name = name
        self.typename = typename


class AllowTypename(Enum):
    DROP_CAMPAIGN_ACL = "DropCampaignACL"


class Allow:
    channels: list[Channel] | None
    is_enabled: bool
    typename: AllowTypename

    def __init__(self, channels: list[Channel] | None, is_enabled: bool, typename: AllowTypename) -> None:
        self.channels = channels
        self.is_enabled = is_enabled
        self.typename = typename


class SelfTypename(Enum):
    DROP_CAMPAIGN_SELF_EDGE = "DropCampaignSelfEdge"


class Self:
    is_account_connected: bool
    typename: SelfTypename

    def __init__(self, is_account_connected: bool, typename: SelfTypename) -> None:
        self.is_account_connected = is_account_connected
        self.typename = typename


class Game:
    id: int
    slug: str
    display_name: str
    typename: ChannelTypename

    def __init__(self, id: int, slug: str, display_name: str, typename: ChannelTypename) -> None:
        self.id = id
        self.slug = slug
        self.display_name = display_name
        self.typename = typename


class PurpleOwner:
    id: UUID | int
    name: str | None
    typename: ChannelTypename
    display_name: str | None
    slug: str | None

    def __init__(
        self,
        id: UUID | int,
        name: str | None,
        typename: ChannelTypename,
        display_name: str | None,
        slug: str | None,
    ) -> None:
        self.id = id
        self.name = name
        self.typename = typename
        self.display_name = display_name
        self.slug = slug


class Status(Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"


class GameClass:
    id: UUID | int
    name: str
    typename: ChannelTypename

    def __init__(self, id: UUID | int, name: str, typename: ChannelTypename) -> None:
        self.id = id
        self.name = name
        self.typename = typename


class BenefitTypename(Enum):
    DROP_BENEFIT = "DropBenefit"


class Benefit:
    id: str
    created_at: datetime
    entitlement_limit: int
    game: GameClass
    image_asset_url: str
    is_ios_available: bool
    name: str
    owner_organization: GameClass
    typename: BenefitTypename

    def __init__(
        self,
        id: str,
        created_at: datetime,
        entitlement_limit: int,
        game: GameClass,
        image_asset_url: str,
        is_ios_available: bool,
        name: str,
        owner_organization: GameClass,
        typename: BenefitTypename,
    ) -> None:
        self.id = id
        self.created_at = created_at
        self.entitlement_limit = entitlement_limit
        self.game = game
        self.image_asset_url = image_asset_url
        self.is_ios_available = is_ios_available
        self.name = name
        self.owner_organization = owner_organization
        self.typename = typename


class BenefitEdgeTypename(Enum):
    DROP_BENEFIT_EDGE = "DropBenefitEdge"


class BenefitEdge:
    benefit: Benefit
    entitlement_limit: int
    typename: BenefitEdgeTypename

    def __init__(self, benefit: Benefit, entitlement_limit: int, typename: BenefitEdgeTypename) -> None:
        self.benefit = benefit
        self.entitlement_limit = entitlement_limit
        self.typename = typename


class TimeBasedDropTypename(Enum):
    TIME_BASED_DROP = "TimeBasedDrop"


class TimeBasedDrop:
    id: UUID
    required_subs: int
    benefit_edges: list[BenefitEdge]
    end_at: datetime
    name: str
    precondition_drops: None
    required_minutes_watched: int
    start_at: datetime
    typename: TimeBasedDropTypename

    def __init__(
        self,
        id: UUID,
        required_subs: int,
        benefit_edges: list[BenefitEdge],
        end_at: datetime,
        name: str,
        precondition_drops: None,
        required_minutes_watched: int,
        start_at: datetime,
        typename: TimeBasedDropTypename,
    ) -> None:
        self.id = id
        self.required_subs = required_subs
        self.benefit_edges = benefit_edges
        self.end_at = end_at
        self.name = name
        self.precondition_drops = precondition_drops
        self.required_minutes_watched = required_minutes_watched
        self.start_at = start_at
        self.typename = typename


class DropCampaignTypename(Enum):
    DROP_CAMPAIGN = "DropCampaign"


class PurpleDropCampaign:
    id: UUID
    drop_campaign_self: Self
    allow: Allow
    account_link_url: str
    description: str
    details_url: str
    end_at: datetime
    event_based_drops: list[Any]
    game: Game
    image_url: str
    name: str
    owner: PurpleOwner
    start_at: datetime
    status: Status
    time_based_drops: list[TimeBasedDrop]
    typename: DropCampaignTypename

    def __init__(
        self,
        id: UUID,
        drop_campaign_self: Self,
        allow: Allow,
        account_link_url: str,
        description: str,
        details_url: str,
        end_at: datetime,
        event_based_drops: list[Any],
        game: Game,
        image_url: str,
        name: str,
        owner: PurpleOwner,
        start_at: datetime,
        status: Status,
        time_based_drops: list[TimeBasedDrop],
        typename: DropCampaignTypename,
    ) -> None:
        self.id = id
        self.drop_campaign_self = drop_campaign_self
        self.allow = allow
        self.account_link_url = account_link_url
        self.description = description
        self.details_url = details_url
        self.end_at = end_at
        self.event_based_drops = event_based_drops
        self.game = game
        self.image_url = image_url
        self.name = name
        self.owner = owner
        self.start_at = start_at
        self.status = status
        self.time_based_drops = time_based_drops
        self.typename = typename


class UserTypename(Enum):
    USER = "User"


class PurpleUser:
    id: int
    drop_campaign: PurpleDropCampaign
    typename: UserTypename

    def __init__(self, id: int, drop_campaign: PurpleDropCampaign, typename: UserTypename) -> None:
        self.id = id
        self.drop_campaign = drop_campaign
        self.typename = typename


class DropCampaign100_Data:
    user: PurpleUser

    def __init__(self, user: PurpleUser) -> None:
        self.user = user


class OperationName(Enum):
    DROP_CAMPAIGN_DETAILS = "DropCampaignDetails"


class Extensions:
    duration_milliseconds: int
    operation_name: OperationName
    request_id: str

    def __init__(self, duration_milliseconds: int, operation_name: OperationName, request_id: str) -> None:
        self.duration_milliseconds = duration_milliseconds
        self.operation_name = operation_name
        self.request_id = request_id


class DropCampaign99:
    data: DropCampaign100_Data
    extensions: Extensions

    def __init__(self, data: DropCampaign100_Data, extensions: Extensions) -> None:
        self.data = data
        self.extensions = extensions


class FluffyDropCampaign:
    id: UUID
    drop_campaign_self: Self
    allow: Allow
    account_link_url: str
    description: str
    details_url: str
    end_at: datetime
    event_based_drops: list[Any]
    game: Game
    image_url: str
    name: str
    owner: GameClass
    start_at: datetime
    status: Status
    time_based_drops: list[TimeBasedDrop]
    typename: DropCampaignTypename

    def __init__(
        self,
        id: UUID,
        drop_campaign_self: Self,
        allow: Allow,
        account_link_url: str,
        description: str,
        details_url: str,
        end_at: datetime,
        event_based_drops: list[Any],
        game: Game,
        image_url: str,
        name: str,
        owner: GameClass,
        start_at: datetime,
        status: Status,
        time_based_drops: list[TimeBasedDrop],
        typename: DropCampaignTypename,
    ) -> None:
        self.id = id
        self.drop_campaign_self = drop_campaign_self
        self.allow = allow
        self.account_link_url = account_link_url
        self.description = description
        self.details_url = details_url
        self.end_at = end_at
        self.event_based_drops = event_based_drops
        self.game = game
        self.image_url = image_url
        self.name = name
        self.owner = owner
        self.start_at = start_at
        self.status = status
        self.time_based_drops = time_based_drops
        self.typename = typename


class FluffyUser:
    id: int
    drop_campaign: FluffyDropCampaign
    typename: UserTypename

    def __init__(self, id: int, drop_campaign: FluffyDropCampaign, typename: UserTypename) -> None:
        self.id = id
        self.drop_campaign = drop_campaign
        self.typename = typename


class DropCampaign109_Data:
    user: FluffyUser

    def __init__(self, user: FluffyUser) -> None:
        self.user = user


class DropCampaign149:
    data: DropCampaign109_Data
    extensions: Extensions

    def __init__(self, data: DropCampaign109_Data, extensions: Extensions) -> None:
        self.data = data
        self.extensions = extensions
