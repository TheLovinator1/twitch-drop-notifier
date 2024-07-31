from django.db import models


class Game(models.Model):
    """The game that the reward is for.

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
        id (UUID): The primary key of the reward.
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

    id = models.UUIDField(primary_key=True)
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

    subs_goal = models.IntegerField(null=True)
    minute_watched_goal = models.IntegerField(null=True)
    typename = models.TextField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.subs_goal} subs and {self.minute_watched_goal} minutes watched"


class RewardCampaign(models.Model):
    """Represents a reward campaign.

    Attributes:
        id (UUID): The primary key of the reward campaign.
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

    id = models.UUIDField(primary_key=True)
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
    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name="reward_campaigns", null=True)
    rewards = models.ManyToManyField(Reward, related_name="reward_campaigns")
    typename = models.TextField(null=True, blank=True)

    def __str__(self) -> str:
        return self.name or "Unknown"
