from __future__ import annotations

import logging
from datetime import datetime
from typing import ClassVar, Self

from asgiref.sync import sync_to_async
from django.contrib.auth.models import AbstractUser
from django.db import models

logger: logging.Logger = logging.getLogger(__name__)


class User(AbstractUser): ...


class Owner(models.Model):
    """The company or person that owns the game.

    Drops will be grouped by the owner. Users can also subscribe to owners.
    """

    # "ad299ac0-f1a5-417d-881d-952c9aed00e9"
    twitch_id = models.TextField(primary_key=True)

    # When the owner was first added to the database.
    created_at = models.DateTimeField(null=True, auto_created=True)

    # When the owner was last modified.
    modified_at = models.DateTimeField(null=True, auto_now=True)

    # "Microsoft"
    name = models.TextField(null=True)

    def __str__(self) -> str:
        return self.name or self.twitch_id

    async def aimport_json(self, data: dict | None) -> Self:
        if not data:
            return self

        if data.get("name") and data["name"] != self.name:
            self.name = data["name"]
            await self.asave()

        return self


class Game(models.Model):
    """This is the game we will see on the front end."""

    # "509658"
    twitch_id = models.TextField(primary_key=True)

    # When the game was first added to the database.
    created_at = models.DateTimeField(null=True, auto_created=True)

    # When the game was last modified.
    modified_at = models.DateTimeField(null=True, auto_now=True)

    # "https://www.twitch.tv/directory/category/halo-infinite"
    game_url = models.URLField(null=True)

    # "Halo Infinite"
    name = models.TextField(null=True)

    # "https://static-cdn.jtvnw.net/ttv-boxart/Halo%20Infinite.jpg"
    box_art_url = models.URLField(null=True)

    # "halo-infinite"
    slug = models.TextField(null=True)

    org = models.ForeignKey(Owner, on_delete=models.CASCADE, related_name="games", null=True)

    def __str__(self) -> str:
        return self.name or self.twitch_id

    async def aimport_json(self, data: dict | None, owner: Owner | None) -> Self:
        # Only update if the data is different.
        dirty = 0

        if not data:
            logger.error("No data provided for %s.", self)
            return self

        if data["__typename"] != "Game":
            logger.error("Not a game? %s", data)
            return self

        if data.get("displayName") and data["displayName"] != self.name:
            self.name = data["displayName"]
            dirty += 1

        if data.get("boxArtURL") and data["boxArtURL"] != self.box_art_url:
            self.box_art_url = data["boxArtURL"]
            dirty += 1

        if data.get("slug") and data["slug"] != self.slug:
            self.slug = data["slug"]
            self.game_url = f"https://www.twitch.tv/directory/game/{data["slug"]}"
            dirty += 1

        if owner:
            await owner.games.aadd(self)  # type: ignore  # noqa: PGH003

        if dirty > 0:
            await self.asave()
            logger.info("Updated game %s", self)

        return self


class DropCampaign(models.Model):
    """This is the drop campaign we will see on the front end."""

    # "f257ce6e-502a-11ef-816e-0a58a9feac02"
    twitch_id = models.TextField(primary_key=True)

    # When the drop campaign was first added to the database.
    created_at = models.DateTimeField(null=True, auto_created=True)

    # When the drop campaign was last modified.
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

    # "https://static-cdn.jtvnw.net/twitch-quests-assets/CAMPAIGN/c8e02666-8b86-471f-bf38-7ece29a758e4.png"
    image_url = models.URLField(null=True)

    # "HCS Open Series - Week 1 - DAY 2 - AUG11"
    name = models.TextField(null=True)

    # "ACTIVE"
    status = models.TextField(null=True)

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="drop_campaigns", null=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["ends_at"]

    def __str__(self) -> str:
        return self.name or self.twitch_id

    async def aimport_json(self, data: dict | None, game: Game | None) -> Self:
        # Only update if the data is different.
        dirty = 0

        if not data:
            logger.error("No data provided for %s.", self)
            return self

        if data.get("__typename") and data["__typename"] != "DropCampaign":
            logger.error("Not a drop campaign? %s", data)
            return self

        if data.get("name") and data["name"] != self.name:
            self.name = data["name"]
            dirty += 1

        if data.get("accountLinkURL") and data["accountLinkURL"] != self.account_link_url:
            self.account_link_url = data["accountLinkURL"]
            dirty += 1

        if data.get("description") and data["description"] != self.description:
            self.description = data["description"]
            dirty += 1

        if data.get("detailsURL") and data["detailsURL"] != self.details_url:
            self.details_url = data["detailsURL"]
            dirty += 1

        end_at_str = data.get("endAt")
        if end_at_str:
            end_at: datetime = datetime.fromisoformat(end_at_str.replace("Z", "+00:00"))
            if end_at != self.ends_at:
                self.ends_at = end_at
                dirty += 1

        start_at_str = data.get("startAt")
        if start_at_str:
            start_at: datetime = datetime.fromisoformat(start_at_str.replace("Z", "+00:00"))
            if start_at != self.starts_at:
                self.starts_at = start_at
                dirty += 1

        status = data.get("status")
        if status and status != self.status and status == "ACTIVE" and self.status != "EXPIRED":
            # If it is EXPIRED, we should not set it to ACTIVE again.
            # TODO(TheLovinator): Set ACTIVE if ACTIVE on Twitch?  # noqa: TD003
            self.status = status
            dirty += 1

        if data.get("imageURL") and data["imageURL"] != self.image_url:
            self.image_url = data["imageURL"]
            dirty += 1

        if game and await sync_to_async(lambda: game != self.game)():
            self.game = game

        if dirty > 0:
            await self.asave()
            logger.info("Updated drop campaign %s", self)

        return self


class TimeBasedDrop(models.Model):
    """This is the drop we will see on the front end."""

    # "d5cdf372-502b-11ef-bafd-0a58a9feac02"
    twitch_id = models.TextField(primary_key=True)

    # When the drop was first added to the database.
    created_at = models.DateTimeField(null=True, auto_created=True)

    # When the drop was last modified.
    modified_at = models.DateTimeField(null=True, auto_now=True)

    # "1"
    required_subs = models.PositiveBigIntegerField(null=True)

    # "2024-08-12T05:59:59.999Z"
    ends_at = models.DateTimeField(null=True)

    # "Cosmic Nexus Chimera"
    name = models.TextField(null=True)

    # "120"
    required_minutes_watched = models.PositiveBigIntegerField(null=True)

    # "2024-08-11T11:00:00Z"
    starts_at = models.DateTimeField(null=True)

    drop_campaign = models.ForeignKey(DropCampaign, on_delete=models.CASCADE, related_name="drops", null=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["required_minutes_watched"]

    def __str__(self) -> str:
        return self.name or self.twitch_id

    async def aimport_json(self, data: dict | None, drop_campaign: DropCampaign | None) -> Self:
        dirty = 0

        if not data:
            logger.error("No data provided for %s.", self)
            return self

        if data.get("__typename") and data["__typename"] != "TimeBasedDrop":
            logger.error("Not a time-based drop? %s", data)
            return self

        if data.get("name") and data["name"] != self.name:
            logger.debug("%s: Old name: %s, new name: %s", self, self.name, data["name"])
            self.name = data["name"]
            dirty += 1

        if data.get("requiredSubs") and data["requiredSubs"] != self.required_subs:
            logger.debug(
                "%s: Old required subs: %s, new required subs: %s",
                self,
                self.required_subs,
                data["requiredSubs"],
            )
            self.required_subs = data["requiredSubs"]
            dirty += 1

        if data.get("requiredMinutesWatched") and data["requiredMinutesWatched"] != self.required_minutes_watched:
            self.required_minutes_watched = data["requiredMinutesWatched"]
            dirty += 1

        start_at_str = data.get("startAt")
        if start_at_str:
            start_at: datetime = datetime.fromisoformat(start_at_str.replace("Z", "+00:00"))
            if start_at != self.starts_at:
                self.starts_at = start_at
                dirty += 1

        end_at_str = data.get("endAt")
        if end_at_str:
            end_at: datetime = datetime.fromisoformat(end_at_str.replace("Z", "+00:00"))
            if end_at != self.ends_at:
                self.ends_at = end_at
                dirty += 1

        if drop_campaign and await sync_to_async(lambda: drop_campaign != self.drop_campaign)():
            self.drop_campaign = drop_campaign
            dirty += 1

        if dirty > 0:
            await self.asave()
            logger.info("Updated time-based drop %s", self)

        return self


class Benefit(models.Model):
    """Benefits are the rewards for the drops."""

    # "d5cdf372-502b-11ef-bafd-0a58a9feac02"
    twitch_id = models.TextField(primary_key=True)

    # When the benefit was first added to the database.
    created_at = models.DateTimeField(null=True, auto_created=True)

    # When the benefit was last modified.
    modified_at = models.DateTimeField(null=True, auto_now=True)

    #  Note: This is Twitch's created_at from the API.
    # "2023-11-09T01:18:00.126Z"
    twitch_created_at = models.DateTimeField(null=True)

    # "1"
    entitlement_limit = models.PositiveBigIntegerField(null=True)

    # "https://static-cdn.jtvnw.net/twitch-quests-assets/REWARD/e58ad175-73f6-4392-80b8-fb0223163733.png"
    image_url = models.URLField(null=True)

    # "True" or "False". None if unknown.
    is_ios_available = models.BooleanField(null=True)

    # "Cosmic Nexus Chimera"
    name = models.TextField(null=True)

    time_based_drop = models.ForeignKey(
        TimeBasedDrop,
        on_delete=models.CASCADE,
        related_name="benefits",
        null=True,
    )

    class Meta:
        ordering: ClassVar[list[str]] = ["-twitch_created_at"]

    def __str__(self) -> str:
        return self.name or self.twitch_id

    async def aimport_json(self, data: dict | None, time_based_drop: TimeBasedDrop | None) -> Self:
        dirty = 0
        if not data:
            logger.error("No data provided for %s.", self)
            return self

        if data.get("__typename") and data["__typename"] != "DropBenefit":
            logger.error("Not a benefit? %s", data)
            return self

        if data.get("name") and data["name"] != self.name:
            self.name = data["name"]
            dirty += 1

        if data.get("imageAssetURL") and data["imageAssetURL"] != self.image_url:
            self.image_url = data["imageAssetURL"]
            dirty += 1

        if data.get("entitlementLimit") and data["entitlementLimit"] != self.entitlement_limit:
            self.entitlement_limit = data["entitlementLimit"]
            dirty += 1

        if data.get("isIOSAvailable") and data["isIOSAvailable"] != self.is_ios_available:
            self.is_ios_available = data["isIOSAvailable"]
            dirty += 1

        twitch_created_at_str = data.get("createdAt")

        if twitch_created_at_str:
            twitch_created_at: datetime = datetime.fromisoformat(twitch_created_at_str.replace("Z", "+00:00"))
            if twitch_created_at != self.twitch_created_at:
                self.twitch_created_at = twitch_created_at
                dirty += 1

        if time_based_drop and await sync_to_async(lambda: time_based_drop != self.time_based_drop)():
            await time_based_drop.benefits.aadd(self)  # type: ignore  # noqa: PGH003
            dirty += 1

        if dirty > 0:
            await self.asave()
            logger.info("Updated benefit %s", self)

        return self


class RewardCampaign(models.Model):
    """Buy subscriptions to earn rewards."""

    # "dc4ff0b4-4de0-11ef-9ec3-621fb0811846"
    twitch_id = models.TextField(primary_key=True)

    # When the reward campaign was first added to the database.
    created_at = models.DateTimeField(null=True, auto_created=True)

    # When the reward campaign was last modified.
    modified_at = models.DateTimeField(null=True, auto_now=True)

    # "Buy 1 new sub, get 3 months of Apple TV+"
    name = models.TextField(null=True)

    # "Apple TV+"
    brand = models.TextField(null=True)

    # "2024-08-11T11:00:00Z"
    starts_at = models.DateTimeField(null=True)

    # "2024-08-12T05:59:59.999Z"
    ends_at = models.DateTimeField(null=True)

    # "UNKNOWN"
    status = models.TextField(null=True)

    # "Get 3 months of Apple TV+ with the purchase of a new sub"
    summary = models.TextField(null=True)

    # "Buy a new sub to get 3 months of Apple TV+"
    instructions = models.TextField(null=True)

    # ""
    reward_value_url_param = models.TextField(null=True)

    # "https://tv.apple.com/includes/commerce/redeem/code-entry"
    external_url = models.URLField(null=True)

    # "https://blog.twitch.tv/2024/07/26/sub-and-get-apple-tv/"
    about_url = models.URLField(null=True)

    # "True" or "False". None if unknown.
    is_site_wide = models.BooleanField(null=True)

    # "1"
    subs_goal = models.PositiveBigIntegerField(null=True)

    # "0"
    minute_watched_goal = models.PositiveBigIntegerField(null=True)

    # "https://static-cdn.jtvnw.net/twitch-quests-assets/CAMPAIGN/quests_appletv_q3_2024/apple_150x200.png"
    image_url = models.URLField(null=True)

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="reward_campaigns", null=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["-starts_at"]

    def __str__(self) -> str:
        return self.name or self.twitch_id

    async def aimport_json(self, data: dict | None) -> Self:
        dirty = 0
        if not data:
            logger.error("No data provided for %s.", self)
            return self

        if data.get("__typename") and data["__typename"] != "RewardCampaign":
            logger.error("Not a reward campaign? %s", data)
            return self

        if data.get("name") and data["name"] != self.name:
            self.name = data["name"]
            dirty += 1

        if data.get("brand") and data["brand"] != self.brand:
            self.brand = data["brand"]
            dirty += 1

        starts_at_str = data.get("startsAt")
        if starts_at_str:
            starts_at: datetime = datetime.fromisoformat(starts_at_str.replace("Z", "+00:00"))
            if starts_at != self.starts_at:
                self.starts_at = starts_at
                dirty += 1

        ends_at_str = data.get("endsAt")
        if ends_at_str:
            ends_at: datetime = datetime.fromisoformat(ends_at_str.replace("Z", "+00:00"))
            if ends_at != self.ends_at:
                self.ends_at = ends_at
                dirty += 1

        if data.get("status") and data["status"] != self.status:
            self.status = data["status"]
            dirty += 1

        if data.get("summary") and data["summary"] != self.summary:
            self.summary = data["summary"]
            dirty += 1

        if data.get("instructions") and data["instructions"] != self.instructions:
            self.instructions = data["instructions"]
            dirty += 1

        if data.get("rewardValueURLParam") and data["rewardValueURLParam"] != self.reward_value_url_param:
            self.reward_value_url_param = data["rewardValueURLParam"]
            logger.warning("What the duck this this? Reward value URL param: %s", self.reward_value_url_param)
            dirty += 1

        if data.get("externalURL") and data["externalURL"] != self.external_url:
            self.external_url = data["externalURL"]
            dirty += 1

        if data.get("aboutURL") and data["aboutURL"] != self.about_url:
            self.about_url = data["aboutURL"]
            dirty += 1

        if data.get("isSitewide") and data["isSitewide"] != self.is_site_wide:
            self.is_site_wide = data["isSitewide"]
            dirty += 1

        subs_goal = data.get("unlockRequirements", {}).get("subsGoal")
        if subs_goal and subs_goal != self.subs_goal:
            self.subs_goal = subs_goal
            dirty += 1

        minutes_watched_goal = data.get("unlockRequirements", {}).get("minuteWatchedGoal")
        if minutes_watched_goal and minutes_watched_goal != self.minute_watched_goal:
            self.minute_watched_goal = minutes_watched_goal
            dirty += 1

        image_url = data.get("image", {}).get("image1xURL")
        if image_url and image_url != self.image_url:
            self.image_url = image_url
            dirty += 1

        if data.get("game") and data["game"].get("id"):
            game, _ = await Game.objects.aget_or_create(twitch_id=data["game"]["id"])
            if await sync_to_async(lambda: game != self.game)():
                await game.reward_campaigns.aadd(self)  # type: ignore  # noqa: PGH003
                dirty += 1

        if "rewards" in data:
            for reward in data["rewards"]:
                reward_instance, created = await Reward.objects.aupdate_or_create(twitch_id=reward["id"])
                await reward_instance.aimport_json(reward, self)
                if created:
                    logger.info("Added reward %s", reward_instance)

        if dirty > 0:
            await self.asave()
            logger.info("Updated reward campaign %s", self)

        return self


class Reward(models.Model):
    """This from the RewardCampaign."""

    # "dc2e9810-4de0-11ef-9ec3-621fb0811846"
    twitch_id = models.TextField(primary_key=True)

    # When the reward was first added to the database.
    created_at = models.DateTimeField(null=True, auto_created=True)

    # When the reward was last modified.
    modified_at = models.DateTimeField(null=True, auto_now=True)

    # "3 months of Apple TV+"
    name = models.TextField(null=True)

    # "https://static-cdn.jtvnw.net/twitch-quests-assets/CAMPAIGN/quests_appletv_q3_2024/apple_200x200.png"
    banner_image_url = models.URLField(null=True)

    # "https://static-cdn.jtvnw.net/twitch-quests-assets/CAMPAIGN/quests_appletv_q3_2024/apple_200x200.png"
    thumbnail_image_url = models.URLField(null=True)

    # "2024-08-19T19:00:00Z"
    earnable_until = models.DateTimeField(null=True)

    # ""
    redemption_instructions = models.TextField(null=True)

    # "https://tv.apple.com/includes/commerce/redeem/code-entry"
    redemption_url = models.URLField(null=True)

    campaign = models.ForeignKey(RewardCampaign, on_delete=models.CASCADE, related_name="rewards", null=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["-earnable_until"]

    def __str__(self) -> str:
        return self.name or "Reward name unknown"

    async def aimport_json(self, data: dict | None, reward_campaign: RewardCampaign | None) -> Self:
        dirty = 0
        if not data:
            logger.error("No data provided for %s.", self)
            return self

        if data.get("__typename") and data["__typename"] != "Reward":
            logger.error("Not a reward? %s", data)
            return self

        if data.get("name") and data["name"] != self.name:
            self.name = data["name"]
            dirty += 1

        earnable_until_str = data.get("earnableUntil")
        if earnable_until_str:
            earnable_until: datetime = datetime.fromisoformat(earnable_until_str.replace("Z", "+00:00"))
            if earnable_until != self.earnable_until:
                self.earnable_until = earnable_until
                dirty += 1

        if data.get("redemptionInstructions") and data["redemptionInstructions"] != self.redemption_instructions:
            # TODO(TheLovinator): We should archive this URL.  # noqa: TD003
            self.redemption_instructions = data["redemptionInstructions"]
            dirty += 1

        if data.get("redemptionURL") and data["redemptionURL"] != self.redemption_url:
            # TODO(TheLovinator): We should archive this URL.  # noqa: TD003
            self.redemption_url = data["redemptionURL"]
            dirty += 1

        banner_image_url = data.get("bannerImage", {}).get("image1xURL")
        if banner_image_url and banner_image_url != self.banner_image_url:
            self.banner_image_url = banner_image_url
            dirty += 1

        thumbnail_image_url = data.get("thumbnailImage", {}).get("image1xURL")
        if thumbnail_image_url and thumbnail_image_url != self.thumbnail_image_url:
            self.thumbnail_image_url = thumbnail_image_url
            dirty += 1

        if reward_campaign and await sync_to_async(lambda: reward_campaign != self.campaign)():
            self.campaign = reward_campaign
            dirty += 1

        if dirty > 0:
            await self.asave()
            logger.info("Updated reward %s", self)

        return self


class Webhook(models.Model):
    """Discord webhook."""

    id = models.TextField(primary_key=True)
    avatar = models.TextField(null=True)
    channel_id = models.TextField(null=True)
    guild_id = models.TextField(null=True)
    name = models.TextField(null=True)
    type = models.TextField(null=True)
    token = models.TextField()
    url = models.TextField()

    # When the webhook was first added to the database.
    created_at = models.DateTimeField(null=True, auto_created=True)

    # When the webhook was last modified.
    modified_at = models.DateTimeField(null=True, auto_now=True)

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
