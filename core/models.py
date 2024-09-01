from __future__ import annotations

import logging
from typing import ClassVar, Self

from django.contrib.auth.models import AbstractUser
from django.db import models

logger: logging.Logger = logging.getLogger(__name__)


class User(AbstractUser): ...


class Owner(models.Model):
    """The company or person that owns the game.

    Drops will be grouped by the owner. Users can also subscribe to owners.
    """

    id = models.TextField(primary_key=True)  # "ad299ac0-f1a5-417d-881d-952c9aed00e9"
    name = models.TextField(null=True)  # "Microsoft"

    def __str__(self) -> str:
        return self.name or "Owner name unknown"

    def import_json(self, data: dict | None) -> Self:
        if not data:
            return self

        self.name = data.get("name", self.name)
        self.save()

        return self


class Game(models.Model):
    """This is the game we will see on the front end."""

    twitch_id = models.TextField(primary_key=True)  # "509658"

    # "https://www.twitch.tv/directory/category/halo-infinite"
    game_url = models.URLField(null=True, default="https://www.twitch.tv/")

    # "Halo Infinite"
    name = models.TextField(null=True, default="Game name unknown")

    # "https://static-cdn.jtvnw.net/ttv-boxart/Halo%20Infinite.jpg"
    box_art_url = models.URLField(null=True, default="https://static-cdn.jtvnw.net/ttv-static/404_boxart.jpg")

    # "halo-infinite"
    slug = models.TextField(null=True)

    org = models.ForeignKey(Owner, on_delete=models.CASCADE, related_name="games", null=True)

    def __str__(self) -> str:
        return self.name or self.twitch_id

    async def import_json(self, data: dict | None, owner: Owner | None) -> Self:
        if not data:
            logger.error("No data provided for %s.", self)
            return self

        self.name = data.get("name", self.name)
        self.box_art_url = data.get("boxArtURL", self.box_art_url)
        self.slug = data.get("slug", self.slug)

        if data.get("slug"):
            self.game_url = f"https://www.twitch.tv/directory/game/{data["slug"]}"

        if owner:
            await owner.games.aadd(self)  # type: ignore  # noqa: PGH003

        self.save()

        return self


class DropCampaign(models.Model):
    """This is the drop campaign we will see on the front end."""

    # "f257ce6e-502a-11ef-816e-0a58a9feac02"
    id = models.TextField(primary_key=True)
    created_at = models.DateTimeField(null=True, auto_created=True)
    modified_at = models.DateTimeField(null=True, auto_now=True)

    # "https://www.halowaypoint.com/settings/linked-accounts"
    account_link_url = models.URLField(null=True)

    # "Tune into this HCS Grassroots event to earn Halo Infinite in-game content!"
    description = models.TextField(null=True)

    # "https://www.halowaypoint.com"
    details_url = models.URLField(null=True)

    # "2024-08-12T05:59:59.999Z"
    ends_at = models.DateTimeField(null=True)
    # "2024-08-11T11:00:00Z""
    starts_at = models.DateTimeField(null=True)

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="drop_campaigns", null=True)

    # "https://static-cdn.jtvnw.net/twitch-quests-assets/CAMPAIGN/c8e02666-8b86-471f-bf38-7ece29a758e4.png"
    image_url = models.URLField(null=True)

    # "HCS Open Series - Week 1 - DAY 2 - AUG11"
    name = models.TextField(null=True, default="Unknown")

    # "ACTIVE"
    status = models.TextField(null=True)

    def __str__(self) -> str:
        return self.name or self.id

    async def import_json(self, data: dict | None, game: Game) -> Self:
        if not data:
            logger.error("No data provided for %s.", self)
            return self

        self.name = data.get("name", self.name)
        self.account_link_url = data.get("accountLinkURL", self.account_link_url)
        self.description = data.get("description", self.description)
        self.details_url = data.get("detailsURL", self.details_url)
        self.ends_at = data.get("endAt", self.ends_at)
        self.starts_at = data.get("startAt", self.starts_at)
        self.status = data.get("status", self.status)
        self.image_url = data.get("imageURL", self.image_url)

        if game:
            self.game = game

        self.save()

        return self


class TimeBasedDrop(models.Model):
    """This is the drop we will see on the front end."""

    id = models.TextField(primary_key=True)  # "d5cdf372-502b-11ef-bafd-0a58a9feac02"
    created_at = models.DateTimeField(null=True, auto_created=True)  # "2024-08-11T00:00:00Z"
    modified_at = models.DateTimeField(null=True, auto_now=True)  # "2024-08-12T00:00:00Z"

    required_subs = models.PositiveBigIntegerField(null=True)  # "1"
    ends_at = models.DateTimeField(null=True)  # "2024-08-12T05:59:59.999Z"
    name = models.TextField(null=True)  # "Cosmic Nexus Chimera"
    required_minutes_watched = models.PositiveBigIntegerField(null=True)  # "120"
    starts_at = models.DateTimeField(null=True)  # "2024-08-11T11:00:00Z"

    drop_campaign = models.ForeignKey(DropCampaign, on_delete=models.CASCADE, related_name="drops", null=True)

    def __str__(self) -> str:
        return self.name or "Drop name unknown"

    async def import_json(self, data: dict | None, drop_campaign: DropCampaign) -> Self:
        if not data:
            logger.error("No data provided for %s.", self)
            return self

        self.name = data.get("name", self.name)
        self.required_subs = data.get("requiredSubs", self.required_subs)
        self.required_minutes_watched = data.get("requiredMinutesWatched", self.required_minutes_watched)
        self.starts_at = data.get("startAt", self.starts_at)
        self.ends_at = data.get("endAt", self.ends_at)

        if drop_campaign:
            self.drop_campaign = drop_campaign

        self.save()

        return self


class Benefit(models.Model):
    """Benefits are the rewards for the drops."""

    id = models.TextField(primary_key=True)  # "d5cdf372-502b-11ef-bafd-0a58a9feac02"
    created_at = models.DateTimeField(null=True, auto_created=True)  # "2024-08-11T00:00:00Z"
    modified_at = models.DateTimeField(null=True, auto_now=True)  # "2024-08-12T00:00:00Z"

    #  Note: This is Twitch's created_at from the API.
    twitch_created_at = models.DateTimeField(null=True)  # "2023-11-09T01:18:00.126Z"

    entitlement_limit = models.PositiveBigIntegerField(null=True)  # "1"

    # "https://static-cdn.jtvnw.net/twitch-quests-assets/REWARD/e58ad175-73f6-4392-80b8-fb0223163733.png"
    image_url = models.URLField(null=True)
    is_ios_available = models.BooleanField(null=True)  # "True"

    name = models.TextField(null=True)  # "Cosmic Nexus Chimera"

    time_based_drop = models.ForeignKey(
        TimeBasedDrop,
        on_delete=models.CASCADE,
        related_name="benefits",
        null=True,
    )

    def __str__(self) -> str:
        return self.name or "Benefit name unknown"

    async def import_json(self, data: dict | None, time_based_drop: TimeBasedDrop) -> Self:
        if not data:
            logger.error("No data provided for %s.", self)
            return self

        self.name = data.get("name", self.name)
        self.entitlement_limit = data.get("entitlementLimit", self.entitlement_limit)
        self.is_ios_available = data.get("isIosAvailable", self.is_ios_available)
        self.image_url = data.get("imageAssetURL", self.image_url)
        self.twitch_created_at = data.get("createdAt", self.twitch_created_at)

        if time_based_drop:
            await time_based_drop.benefits.aadd(self)  # type: ignore  # noqa: PGH003

        self.save()

        return self


class RewardCampaign(models.Model):
    """Buy subscriptions to earn rewards."""

    id = models.TextField(primary_key=True)  # "dc4ff0b4-4de0-11ef-9ec3-621fb0811846"
    created_at = models.DateTimeField(null=True, auto_created=True)  # "2024-08-11T00:00:00Z"
    modified_at = models.DateTimeField(null=True, auto_now=True)  # "2024-08-12T00:00:00Z"

    name = models.TextField(null=True)  # "Buy 1 new sub, get 3 months of Apple TV+"
    brand = models.TextField(null=True)  # "Apple TV+"
    starts_at = models.DateTimeField(null=True)  # "2024-08-11T11:00:00Z"
    ends_at = models.DateTimeField(null=True)  # "2024-08-12T05:59:59.999Z"
    status = models.TextField(null=True)  # "UNKNOWN"
    summary = models.TextField(null=True)  # "Get 3 months of Apple TV+ with the purchase of a new sub"
    instructions = models.TextField(null=True)  # "Buy a new sub to get 3 months of Apple TV+"
    reward_value_url_param = models.TextField(null=True)  # ""
    external_url = models.URLField(null=True)  # "https://tv.apple.com/includes/commerce/redeem/code-entry"
    about_url = models.URLField(null=True)  # "https://blog.twitch.tv/2024/07/26/sub-and-get-apple-tv/"
    is_site_wide = models.BooleanField(null=True)  # "True"
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="reward_campaigns", null=True)

    sub_goal = models.PositiveBigIntegerField(null=True)  # "1"
    minute_watched_goal = models.PositiveBigIntegerField(null=True)  # "0"

    # "https://static-cdn.jtvnw.net/twitch-quests-assets/CAMPAIGN/quests_appletv_q3_2024/apple_150x200.png"
    image_url = models.URLField(null=True)

    def __str__(self) -> str:
        return self.name or "Reward campaign name unknown"

    async def import_json(self, data: dict | None) -> Self:
        if not data:
            logger.error("No data provided for %s.", self)
            return self

        self.name = data.get("name", self.name)
        self.brand = data.get("brand", self.brand)
        self.starts_at = data.get("startsAt", self.starts_at)
        self.ends_at = data.get("endsAt", self.ends_at)
        self.status = data.get("status", self.status)
        self.summary = data.get("summary", self.summary)
        self.instructions = data.get("instructions", self.instructions)
        self.reward_value_url_param = data.get("rewardValueURLParam", self.reward_value_url_param)
        self.external_url = data.get("externalURL", self.external_url)
        self.about_url = data.get("aboutURL", self.about_url)
        self.is_site_wide = data.get("isSiteWide", self.is_site_wide)

        unlock_requirements: dict = data.get("unlockRequirements", {})
        if unlock_requirements:
            self.sub_goal = unlock_requirements.get("subsGoal", self.sub_goal)
            self.minute_watched_goal = unlock_requirements.get("minuteWatchedGoal", self.minute_watched_goal)

        image = data.get("image", {})
        if image:
            self.image_url = image.get("image1xURL", self.image_url)

        if data.get("game"):
            game: Game | None = Game.objects.filter(twitch_id=data["game"]["id"]).first()
            if game:
                await game.reward_campaigns.aadd(self)  # type: ignore  # noqa: PGH003

        self.save()

        return self


class Reward(models.Model):
    """This from the RewardCampaign."""

    id = models.TextField(primary_key=True)  # "dc2e9810-4de0-11ef-9ec3-621fb0811846"
    name = models.TextField(null=True)  # "3 months of Apple TV+"

    # "https://static-cdn.jtvnw.net/twitch-quests-assets/CAMPAIGN/quests_appletv_q3_2024/apple_200x200.png"
    banner_image_url = models.URLField(null=True)
    # "https://static-cdn.jtvnw.net/twitch-quests-assets/CAMPAIGN/quests_appletv_q3_2024/apple_200x200.png"
    thumbnail_image_url = models.URLField(null=True)

    earnable_until = models.DateTimeField(null=True)  # "2024-08-19T19:00:00Z"
    redemption_instructions = models.TextField(null=True)  # ""
    redemption_url = models.URLField(null=True)  # "https://tv.apple.com/includes/commerce/redeem/code-entry"

    campaign = models.ForeignKey(RewardCampaign, on_delete=models.CASCADE, related_name="rewards", null=True)

    def __str__(self) -> str:
        return self.name or "Reward name unknown"

    async def import_json(self, data: dict | None, reward_campaign: RewardCampaign) -> Self:
        if not data:
            logger.error("No data provided for %s.", self)
            return self

        self.name = data.get("name", self.name)
        self.earnable_until = data.get("earnableUntil", self.earnable_until)
        self.redemption_instructions = data.get("redemptionInstructions", self.redemption_instructions)
        self.redemption_url = data.get("redemptionURL", self.redemption_url)

        banner_image = data.get("bannerImage", {})
        if banner_image:
            self.banner_image_url = banner_image.get("image1xURL", self.banner_image_url)

        thumbnail_image = data.get("thumbnailImage", {})
        if thumbnail_image:
            self.thumbnail_image_url = thumbnail_image.get("image1xURL", self.thumbnail_image_url)

        if reward_campaign:
            self.campaign = reward_campaign

        self.save()

        return self


class Webhook(models.Model):
    """Discord webhook."""

    avatar = models.TextField(null=True)
    channel_id = models.TextField(null=True)
    guild_id = models.TextField(null=True)
    id = models.TextField(primary_key=True)
    name = models.TextField(null=True)
    type = models.TextField(null=True)
    token = models.TextField()
    url = models.TextField()

    # Get notified when the site finds a new game.
    subscribed_new_games = models.ManyToManyField(Game, related_name="subscribed_new_games")

    # Get notified when a drop goes live.
    subscribed_live_games = models.ManyToManyField(Game, related_name="subscribed_live_games")

    # Get notified when the site finds a new drop campaign for a specific organization.
    subscribed_new_owners = models.ManyToManyField(Owner, related_name="subscribed_new_owners")

    # Get notified when a drop goes live for a specific organization.
    subscribed_live_owners = models.ManyToManyField(Owner, related_name="subscribed_live_owners")

    # So we don't spam the same drop campaign over and over.
    seen_drops = models.ManyToManyField(DropCampaign, related_name="seen_drops")

    class Meta:
        unique_together: ClassVar[list[str]] = ["id", "token"]

    def __str__(self) -> str:
        return f"{self.name} - {self.get_webhook_url()}"

    def get_webhook_url(self) -> str:
        try:
            return f"https://discord.com/api/webhooks/{self.id}/{self.token}"
        except AttributeError:
            return ""
