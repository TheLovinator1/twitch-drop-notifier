from django.db import models


class Game(models.Model):
    """The game that the reward is for.

    Used for reward campaigns (buy subs) and drop campaigns (watch games).

    Attributes:
        id (int): The primary key of the game.
        slug (str): The slug identifier of the game.
        display_name (str): The display name of the game.
        typename (str): The type name of the object, typically "Game".

    JSON example:
        {
            "id": "780302568",
            "slug": "xdefiant",
            "displayName": "XDefiant",
            "__typename": "Game"
        }
    """

    id = models.AutoField(primary_key=True)
    slug = models.TextField(null=True, blank=True)
    display_name = models.TextField(null=True, blank=True)
    typename = models.TextField(null=True, blank=True)

    def __str__(self) -> str:
        return self.display_name or "Unknown"

    def get_twitch_url(self) -> str:
        return f"https://www.twitch.tv/directory/game/{self.slug}"


class Image(models.Model):
    """An image model representing URLs and type.

    Attributes:
        image1_x_url (str): URL to the image.
        typename (str): The type name of the object, typically "RewardCampaignImageSet".

    JSON example:
        {
            "image1xURL": "https://static-cdn.jtvnw.net/twitch-quests-assets/CAMPAIGN/quests_xdefiant_q3_2024/campaign.png",
            "__typename": "RewardCampaignImageSet"
        }
    """

    image1_x_url = models.URLField(null=True, blank=True)
    typename = models.TextField(null=True, blank=True)

    def __str__(self) -> str:
        return self.image1_x_url or "Unknown"


class Reward(models.Model):
    """The actual reward you get when you complete the requirements.

    Attributes:
        id (str): The primary key of the reward.
        name (str): The name of the reward.
        banner_image (Image): The banner image associated with the reward.
        thumbnail_image (Image): The thumbnail image associated with the reward.
        earnable_until (datetime): The date and time until the reward can be earned.
        redemption_instructions (str): Instructions on how to redeem the reward.
        redemption_url (str): URL for redeeming the reward.
        typename (str): The type name of the object, typically "Reward".

    JSON example:
        {
            "id": "374628c6-34b4-11ef-a468-62ece0f03426",
            "name": "Twitchy Character Skin",
            "bannerImage": {
                "image1xURL": "https://static-cdn.jtvnw.net/twitch-quests-assets/CAMPAIGN/quests_xdefiant_q3_2024/reward.png",
                "__typename": "RewardCampaignImageSet"
            },
            "thumbnailImage": {
                "image1xURL": "https://static-cdn.jtvnw.net/twitch-quests-assets/CAMPAIGN/quests_xdefiant_q3_2024/reward.png",
                "__typename": "RewardCampaignImageSet"
            },
            "earnableUntil": "2024-07-30T06:59:59Z",
            "redemptionInstructions": "",
            "redemptionURL": "https://redeem.ubisoft.com/xdefiant/",
            "__typename": "Reward"
        }
    """

    id = models.TextField(primary_key=True)
    name = models.TextField(null=True, blank=True)
    banner_image = models.ForeignKey(Image, related_name="banner_rewards", on_delete=models.CASCADE, null=True)
    thumbnail_image = models.ForeignKey(Image, related_name="thumbnail_rewards", on_delete=models.CASCADE, null=True)
    earnable_until = models.DateTimeField(null=True)
    redemption_instructions = models.TextField(null=True, blank=True)
    redemption_url = models.URLField(null=True, blank=True)
    typename = models.TextField(null=True, blank=True)

    def __str__(self) -> str:
        return self.name or "Unknown"


class UnlockRequirements(models.Model):
    """Requirements to unlock a reward.

    Attributes:
        subs_goal (int): The number of subscriptions needed to unlock the reward.
        minute_watched_goal (int): The number of minutes watched needed to unlock the reward.
        typename (str): The type name of the object, typically "QuestRewardUnlockRequirements".

    JSON example:
        {
            "subsGoal": 2,
            "minuteWatchedGoal": 0,
            "__typename": "QuestRewardUnlockRequirements"
        }
    """

    subs_goal = models.PositiveBigIntegerField(null=True)
    minute_watched_goal = models.PositiveBigIntegerField(null=True)
    typename = models.TextField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.subs_goal} subs and {self.minute_watched_goal} minutes watched"


class RewardCampaign(models.Model):
    """Represents a reward campaign.

    Attributes:
        id (str): The primary key of the reward campaign.
        name (str): The name of the reward campaign.
        brand (str): The brand associated with the campaign.
        starts_at (datetime): The start date and time of the campaign.
        ends_at (datetime): The end date and time of the campaign.
        status (str): The status of the campaign.
        summary (str): A brief summary of the campaign.
        instructions (str): Instructions for the campaign.
        external_url (str): The external URL related to the campaign.
        reward_value_url_param (str): URL parameter for the reward value.
        about_url (str): URL with more information about the campaign.
        is_sitewide (bool): Indicates if the campaign is sitewide.
        game (Game): The game associated with the campaign.
        image (Image): The image associated with the campaign.
        rewards (ManyToManyField): The rewards available in the campaign.
        typename (str): The type name of the object, typically "RewardCampaign".

    JSON example:
        {
            "id": "3757a2ae-34b4-11ef-a468-62ece0f03426",
            "name": "XDefiant Season 1 Launch",
            "brand": "Ubisoft",
            "startsAt": "2024-07-02T17:00:00Z",
            "endsAt": "2024-07-30T06:59:59Z",
            "status": "UNKNOWN",
            "summary": "Get a redeemable code for the Twitchy Character Skin in XDefiant for gifting or purchasing 2 subscriptions of any tier to participating channels.",
            "instructions": "",
            "externalURL": "https://redeem.ubisoft.com/xdefiant/",
            "rewardValueURLParam": "",
            "aboutURL": "https://xdefiant.com/S1-twitch-rewards",
            "isSitewide": false,
            "game": {
                "id": "780302568",
                "slug": "xdefiant",
                "displayName": "XDefiant",
                "__typename": "Game"
            },
            "unlockRequirements": {
                    "subsGoal": 2,
                    "minuteWatchedGoal": 0,
                    "__typename": "QuestRewardUnlockRequirements"
            },
            "image": {
                "image1xURL": "https://static-cdn.jtvnw.net/twitch-quests-assets/CAMPAIGN/quests_xdefiant_q3_2024/campaign.png",
                "__typename": "RewardCampaignImageSet"
            },
            "rewards": [
                {
                    "id": "374628c6-34b4-11ef-a468-62ece0f03426",
                    "name": "Twitchy Character Skin",
                    "bannerImage": {
                        "image1xURL": "https://static-cdn.jtvnw.net/twitch-quests-assets/CAMPAIGN/quests_xdefiant_q3_2024/reward.png",
                        "__typename": "RewardCampaignImageSet"
                    },
                    "thumbnailImage": {
                        "image1xURL": "https://static-cdn.jtvnw.net/twitch-quests-assets/CAMPAIGN/quests_xdefiant_q3_2024/reward.png",
                        "__typename": "RewardCampaignImageSet"
                    },
                    "earnableUntil": "2024-07-30T06:59:59Z",
                    "redemptionInstructions": "",
                    "redemptionURL": "https://redeem.ubisoft.com/xdefiant/",
                    "__typename": "Reward"
                }
            ],
            "__typename": "RewardCampaign"
        }
    """  # noqa: E501

    id = models.TextField(primary_key=True)
    name = models.TextField(null=True, blank=True)
    brand = models.TextField(null=True, blank=True)
    starts_at = models.DateTimeField(null=True)
    ends_at = models.DateTimeField(null=True)
    status = models.TextField(null=True, blank=True)
    summary = models.TextField(null=True, blank=True)
    instructions = models.TextField(null=True, blank=True)
    external_url = models.URLField(null=True, blank=True)
    reward_value_url_param = models.TextField(null=True, blank=True)
    about_url = models.URLField(null=True, blank=True)
    is_sitewide = models.BooleanField(null=True)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="reward_campaigns", null=True)
    unlock_requirements = models.ForeignKey(
        UnlockRequirements,
        on_delete=models.CASCADE,
        related_name="reward_campaigns",
        null=True,
    )
    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name="reward_campaigns", null=True)
    rewards = models.ManyToManyField(Reward, related_name="reward_campaigns")
    typename = models.TextField(null=True, blank=True)

    def __str__(self) -> str:
        return self.name or "Unknown"


class Channel(models.Model):
    """Represents a Twitch channel.

    Attributes:
        id (int): The primary key of the channel.
        display_name (str): The display name of the channel.
        name (str): The name of the channel.
        typename (str): The type name of the object, typically "Channel".

    JSON example:
        {
            "id": "25254906",
            "displayName": "Stresss",
            "name": "stresss",
            "__typename": "Channel"
        }
    """

    id = models.PositiveBigIntegerField(primary_key=True)
    display_name = models.TextField(null=True, blank=True)
    name = models.TextField(null=True, blank=True)
    typename = models.TextField(null=True, blank=True)

    def __str__(self) -> str:
        return self.display_name or "Unknown"

    def get_twitch_url(self) -> str:
        return f"https://www.twitch.tv/{self.name}"


class Allow(models.Model):
    """List of channels that you can watch to earn rewards.

    Attributes:
        channels (ManyToManyField): The channels that you can watch to earn rewards.
        is_enabled (bool): Indicates if the channel is enabled.
        typename (str): The type name of the object, typically "RewardCampaignChannelAllow".

    JSON example:
        "allow": {
            "channels": [
                {
                    "id": "25254906",
                    "displayName": "Stresss",
                    "name": "stresss",
                    "__typename": "Channel"
                }
                ],
            "isEnabled": false,
            "__typename": "DropCampaignACL"
        },
    """

    channels = models.ManyToManyField(Channel, related_name="allow")
    is_enabled = models.BooleanField(default=True)
    typename = models.TextField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.channels.count()} channels"


class Owner(models.Model):
    """Represents the owner of the reward campaign.

    Attributes:
        id (int): The primary key of the owner.
        slug (str): The slug identifier of the owner.
        display_name (str): The display name of the owner.
        typename (str): The type name of the object, typically "Organization".

    JSON example:
        "game": {
            "id": "491487",
            "slug": "dead-by-daylight",
            "displayName": "Dead by Daylight",
            "__typename": "Game"
        },"
    """

    id = models.PositiveBigIntegerField(primary_key=True)
    slug = models.TextField(null=True, blank=True)
    display_name = models.TextField(null=True, blank=True)
    typename = models.TextField(null=True, blank=True)

    def __str__(self) -> str:
        return self.display_name or "Unknown"

    def get_twitch_url(self) -> str:
        return f"https://www.twitch.tv/{self.slug}"


class Benefit(models.Model):
    """Represents a benefit that you can earn.

    Attributes:
        id (int): The primary key of the benefit.
        created_at (datetime): The date and time the benefit was created.
        entitlement_limit (int): The limit of entitlement.
        game (Game): The game associated with the benefit.
        image_asset_url (str): URL to the image asset.
        is_ios_available (bool): Indicates if the benefit is available on iOS.
        name (str): The name of the benefit.
        owner_organization (Owner): The owner organization of the benefit.
        typename (str): The type name of the object, typically "Benefit".

    JSON example:
        "benefit": {
            "id": "6da09649-1fda-4446-a061-cacd8e21b886_CUSTOM_ID_S29_Torso008_01",
            "createdAt": "2024-07-09T12:57:31.072Z",
            "entitlementLimit": 1,
            "game": {
                "id": "491487",
                "name": "Dead by Daylight",
                "__typename": "Game"
            },
            "imageAssetURL": "https://static-cdn.jtvnw.net/twitch-quests-assets/REWARD/ed4a7829-cc2b-44d3-90a4-f73ef7d8d636.png",
            "isIosAvailable": false,
            "name": "Unwanted Attention",
            "ownerOrganization": {
                "id": "6da09649-1fda-4446-a061-cacd8e21b886",
                "name": "Behaviour Interactive Inc.",
                "__typename": "Organization"
            },
            "__typename": "DropBenefit"
        }
    """

    id = models.TextField(primary_key=True)
    created_at = models.DateTimeField(null=True)
    entitlement_limit = models.PositiveBigIntegerField(null=True)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="benefits", null=True)
    image_asset_url = models.URLField(null=True, blank=True)
    is_ios_available = models.BooleanField(null=True)
    name = models.TextField(null=True, blank=True)
    owner_organization = models.ForeignKey(Owner, on_delete=models.CASCADE, related_name="benefits", null=True)
    typename = models.TextField(null=True, blank=True)

    def __str__(self) -> str:
        return self.name or "Unknown"


class BenefitEdge(models.Model):
    """Represents a benefit edge.

    Attributes:
        benefit (Benefit): The benefit associated with the edge.
        entitlement_limit (int): The limit of entitlement.
        typename (str): The type name of the object, typically "DropBenefitEdge".


    JSON example:
        "benefitEdges": [
            {
                "benefit": {
                    "id": "6da09649-1fda-4446-a061-cacd8e21b886_CUSTOM_ID_S29_Torso008_01",
                    "createdAt": "2024-07-09T12:57:31.072Z",
                    "entitlementLimit": 1,
                    "game": {
                        "id": "491487",
                        "name": "Dead by Daylight",
                        "__typename": "Game"
                    },
                    "imageAssetURL": "https://static-cdn.jtvnw.net/twitch-quests-assets/REWARD/ed4a7829-cc2b-44d3-90a4-f73ef7d8d636.png",
                    "isIosAvailable": false,
                    "name": "Unwanted Attention",
                    "ownerOrganization": {
                        "id": "6da09649-1fda-4446-a061-cacd8e21b886",
                        "name": "Behaviour Interactive Inc.",
                        "__typename": "Organization"
                    },
                    "__typename": "DropBenefit"
                },
                "entitlementLimit": 1,
                "__typename": "DropBenefitEdge"
            }
        ],
    """

    benefit = models.ForeignKey(Benefit, on_delete=models.CASCADE, related_name="benefit_edges", null=True)
    entitlement_limit = models.PositiveBigIntegerField(null=True)
    typename = models.TextField(null=True, blank=True)

    def __str__(self) -> str:
        benefit_name: str | None = self.benefit.name if self.benefit else "Unknown"
        return f"{benefit_name} - {self.entitlement_limit}"


class TimeBasedDrop(models.Model):
    """Represents a time-based drop.

    Attributes:
        id (int): The primary key of the time-based drop.
        name (str): The name of the time-based drop.
        starts_at (datetime): The start date and time of the drop.
        ends_at (datetime): The end date and time of the drop.
        typename (str): The type name of the object, typically "TimeBasedDrop".

    JSON example:
        {
            "id": "0ebeff68-3df3-11ef-b15b-0a58a9feac02",
            "requiredSubs": 0,
            "benefitEdges": [
                {
                    "benefit": {
                        "id": "6da09649-1fda-4446-a061-cacd8e21b886_CUSTOM_ID_S29_Legs008_01",
                        "createdAt": "2024-07-09T12:58:03.654Z",
                        "entitlementLimit": 1,
                        "game": {
                            "id": "491487",
                            "name": "Dead by Daylight",
                            "__typename": "Game"
                        },
                        "imageAssetURL": "https://static-cdn.jtvnw.net/twitch-quests-assets/REWARD/f46acdf5-9515-41eb-805e-86956db0a9e9.png",
                        "isIosAvailable": false,
                        "name": "Back Home",
                        "ownerOrganization": {
                            "id": "6da09649-1fda-4446-a061-cacd8e21b886",
                            "name": "Behaviour Interactive Inc.",
                            "__typename": "Organization"
                        },
                        "__typename": "DropBenefit"
                    },
                    "entitlementLimit": 1,
                    "__typename": "DropBenefitEdge"
                }
            ],
            "endAt": "2024-07-30T14:59:59.999Z",
            "name": "Back Home",
            "preconditionDrops": null,
            "requiredMinutesWatched": 360,
            "startAt": "2024-07-16T15:00:00Z",
            "__typename": "TimeBasedDrop"
        },
    """

    id = models.TextField(primary_key=True)
    created_at = models.DateTimeField(null=True)
    entitlement_limit = models.PositiveBigIntegerField(null=True)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="time_based_drops", null=True)
    image_asset_url = models.URLField(null=True, blank=True)
    is_ios_available = models.BooleanField(null=True)
    name = models.TextField(null=True, blank=True)
    owner_organization = models.ForeignKey(Owner, on_delete=models.CASCADE, related_name="time_based_drops", null=True)
    typename = models.TextField(null=True, blank=True)

    def __str__(self) -> str:
        return self.name or "Unknown"


class DropCampaign(models.Model):
    """Represents a drop campaign.

    Attributes:
        id (int): The primary key of the drop campaign.
        allow (Allow): The channels that you can watch to earn rewards.
        account_link_url (str): URL to link your account.
        description (str): The description of the drop campaign.
        details_url (str): URL with more details about the drop campaign.
        ends_at (datetime): The end date and time of the drop campaign.
        game (Game): The game associated with the drop campaign.
        image_url (str): URL to the image associated with the drop campaign.
        name (str): The name of the drop campaign.
        owner (Owner): The owner of the drop campaign.
        starts_at (datetime): The start date and time of the drop campaign.
        status (str): The status of the drop campaign.
        time_based_drops (ManyToManyField): The time-based drops associated with the campaign.
        typename (str): The type name of the object, typically "DropCampaign".
    """

    id = models.TextField(primary_key=True)
    allow = models.ForeignKey(Allow, on_delete=models.CASCADE, related_name="drop_campaigns", null=True)
    account_link_url = models.URLField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    details_url = models.URLField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True)
    # event_based_drops =  ????
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="drop_campaigns", null=True)
    image_url = models.URLField(null=True, blank=True)
    name = models.TextField(null=True, blank=True)
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE, related_name="drop_campaigns", null=True)
    starts_at = models.DateTimeField(null=True)
    status = models.TextField(null=True, blank=True)
    time_based_drops = models.ManyToManyField(TimeBasedDrop, related_name="drop_campaigns")
    typename = models.TextField(null=True, blank=True)

    def __str__(self) -> str:
        return self.name or "Unknown"
