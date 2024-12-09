from __future__ import annotations

import logging
from typing import ClassVar, Self

from django.contrib.auth.models import AbstractUser
from django.db import models

from core.models_utils import update_fields, wrong_typename

logger: logging.Logger = logging.getLogger(__name__)


class User(AbstractUser):
    """Custom user model."""

    class Meta:
        ordering: ClassVar[list[str]] = ["username"]

    def __str__(self) -> str:
        """Return the username."""
        return self.username


class ScrapedJson(models.Model):
    """The JSON data from the Twitch API.

    This data is from https://github.com/TheLovinator1/TwitchDropsMiner.
    """

    json_data = models.JSONField(unique=True, help_text="The JSON data from the Twitch API.")
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    imported_at = models.DateTimeField(null=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["-created_at"]

    def __str__(self) -> str:
        """Return the created at date and optionally if not imported yet."""
        return f"{'' if self.imported_at else 'Not imported - '}{self.created_at}"


class Owner(models.Model):
    """The company or person that owns the game.

    Drops will be grouped by the owner. Users can also subscribe to owners.
    """

    # "ad299ac0-f1a5-417d-881d-952c9aed00e9"
    twitch_id = models.TextField(primary_key=True)

    # When the owner was first added to the database.
    created_at = models.DateTimeField(auto_created=True)

    # When the owner was last modified.
    modified_at = models.DateTimeField(auto_now=True)

    # "Microsoft"
    name = models.TextField(blank=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["name"]

    def __str__(self) -> str:
        """Return the name of the owner."""
        return f"{self.name or self.twitch_id} - {self.created_at}"

    def import_json(self, data: dict) -> Self:
        """Import the data from the Twitch API."""
        if wrong_typename(data, "Organization"):
            return self

        field_mapping: dict[str, str] = {"name": "name"}
        updated: int = update_fields(instance=self, data=data, field_mapping=field_mapping)
        if updated > 0:
            logger.info("Updated %s fields for %s", updated, self)

        return self


class Game(models.Model):
    """The game the drop campaign is for. Note that some reward campaigns are not tied to a game."""

    # "509658"
    twitch_id = models.TextField(primary_key=True)

    # When the game was first added to the database.
    created_at = models.DateTimeField(auto_created=True)

    # When the game was last modified.
    modified_at = models.DateTimeField(auto_now=True)

    # "https://www.twitch.tv/directory/category/halo-infinite"
    game_url = models.URLField(blank=True)

    # "Halo Infinite"
    name = models.TextField(blank=True)

    # "https://static-cdn.jtvnw.net/ttv-boxart/Halo%20Infinite.jpg"
    box_art_url = models.URLField(blank=True)

    # "halo-infinite"
    slug = models.TextField(blank=True)

    # The owner of the game.
    # This is optional because some games are not tied to an owner.
    org = models.ForeignKey(Owner, on_delete=models.CASCADE, related_name="games", null=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["name"]

    def __str__(self) -> str:
        """Return the name of the game and when it was created."""
        return f"{self.name or self.twitch_id} - {self.created_at}"

    def import_json(self, data: dict, owner: Owner | None) -> Self:
        """Import the data from the Twitch API."""
        if wrong_typename(data, "Game"):
            return self

        # Map the fields from the JSON data to the Django model fields.
        field_mapping: dict[str, str] = {
            "displayName": "name",
            "boxArtURL": "box_art_url",
            "slug": "slug",
        }
        updated: int = update_fields(instance=self, data=data, field_mapping=field_mapping)

        if updated > 0:
            logger.info("Updated %s fields for %s", updated, self)

        if not owner:
            logger.error("Owner is required for %s", self)
            return self

        # Update the owner if the owner is different or not set.
        if owner != self.org:
            self.org = owner
            logger.info("Updated owner %s for %s", owner, self)
            self.save()

        return self


class DropCampaign(models.Model):
    """This is the drop campaign we will see on the front end."""

    # "f257ce6e-502a-11ef-816e-0a58a9feac02"
    twitch_id = models.TextField(primary_key=True)

    # When the drop campaign was first added to the database.
    created_at = models.DateTimeField(auto_created=True)

    # When the drop campaign was last modified.
    modified_at = models.DateTimeField(auto_now=True)

    # "https://www.halowaypoint.com/settings/linked-accounts"
    account_link_url = models.URLField(blank=True)

    # "Tune into this HCS Grassroots event to earn Halo Infinite in-game content!"
    description = models.TextField(blank=True)

    # "https://www.halowaypoint.com"
    details_url = models.URLField(blank=True)

    # "2024-08-12T05:59:59.999Z"
    ends_at = models.DateTimeField(null=True)

    # "2024-08-11T11:00:00Z""
    starts_at = models.DateTimeField(null=True)

    # "https://static-cdn.jtvnw.net/twitch-quests-assets/CAMPAIGN/c8e02666-8b86-471f-bf38-7ece29a758e4.png"
    image_url = models.URLField(blank=True)

    # "HCS Open Series - Week 1 - DAY 2 - AUG11"
    name = models.TextField(blank=True)

    # "ACTIVE"
    status = models.TextField(blank=True)

    # The game this drop campaign is for.
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="drop_campaigns", null=True)

    # The JSON data from the Twitch API.
    # We use this to find out where the game came from.
    scraped_json = models.ForeignKey(
        ScrapedJson,
        null=True,
        on_delete=models.SET_NULL,
        help_text="Reference to the JSON data from the Twitch API.",
    )

    class Meta:
        ordering: ClassVar[list[str]] = ["ends_at"]

    def __str__(self) -> str:
        """Return the name of the drop campaign and when it was created."""
        return f"{self.name or self.twitch_id} - {self.created_at}"

    def import_json(self, data: dict, game: Game | None, *, scraping_local_files: bool = False) -> Self:
        """Import the data from the Twitch API.

        Args:
            data (dict | None): The data from the Twitch API.
            game (Game | None): The game this drop campaign is for.
            scraping_local_files (bool, optional): If this was scraped from local data. Defaults to True.

        Returns:
            Self: The updated drop campaign.
        """
        if wrong_typename(data, "DropCampaign"):
            return self

        field_mapping: dict[str, str] = {
            "name": "name",
            "accountLinkURL": "account_link_url",  # TODO(TheLovinator): Should archive site.  # noqa: TD003
            "description": "description",
            "endAt": "ends_at",
            "startAt": "starts_at",
            "detailsURL": "details_url",  # TODO(TheLovinator): Should archive site.  # noqa: TD003
            "imageURL": "image_url",
        }

        updated: int = update_fields(instance=self, data=data, field_mapping=field_mapping)
        if updated > 0:
            logger.info("Updated %s fields for %s", updated, self)

        # Update the drop campaign's status if the new status is different.
        # When scraping local files:
        #    - Only update if the status changes from "ACTIVE" to "EXPIRED".
        # When scraping from the Twitch API:
        #    - Always update the status regardless of its value.
        status = data.get("status")
        if status and status != self.status:
            # Check if scraping local files and status changes from ACTIVE to EXPIRED
            should_update = scraping_local_files and status == "EXPIRED" and self.status == "ACTIVE"

            # Always update if not scraping local files
            if not scraping_local_files or should_update:
                self.status = status
                self.save()

        # Update the game if the game is different or not set.
        if game and game != self.game:
            self.game = game
            logger.info("Updated game %s for %s", game, self)
            self.save()

        return self


class TimeBasedDrop(models.Model):
    """This is the drop we will see on the front end."""

    # "d5cdf372-502b-11ef-bafd-0a58a9feac02"
    twitch_id = models.TextField(primary_key=True)

    # When the drop was first added to the database.
    created_at = models.DateTimeField(auto_created=True)

    # When the drop was last modified.
    modified_at = models.DateTimeField(auto_now=True)

    # "1"
    required_subs = models.PositiveBigIntegerField(null=True)

    # "2024-08-12T05:59:59.999Z"
    ends_at = models.DateTimeField(null=True)

    # "Cosmic Nexus Chimera"
    name = models.TextField(blank=True)

    # "120"
    required_minutes_watched = models.PositiveBigIntegerField(null=True)

    # "2024-08-11T11:00:00Z"
    starts_at = models.DateTimeField(null=True)

    drop_campaign = models.ForeignKey(DropCampaign, on_delete=models.CASCADE, related_name="drops", null=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["required_minutes_watched"]

    def __str__(self) -> str:
        """Return the name of the drop and when it was created."""
        return f"{self.name or self.twitch_id} - {self.created_at}"

    def import_json(self, data: dict, drop_campaign: DropCampaign | None) -> Self:
        """Import the data from the Twitch API."""
        if wrong_typename(data, "TimeBasedDrop"):
            return self

        field_mapping: dict[str, str] = {
            "name": "name",
            "requiredSubs": "required_subs",
            "requiredMinutesWatched": "required_minutes_watched",
            "startAt": "starts_at",
            "endAt": "ends_at",
        }

        updated: int = update_fields(instance=self, data=data, field_mapping=field_mapping)
        if updated > 0:
            logger.info("Updated %s fields for %s", updated, self)

        if drop_campaign and drop_campaign != self.drop_campaign:
            self.drop_campaign = drop_campaign
            logger.info("Updated drop campaign %s for %s", drop_campaign, self)
            self.save()

        return self


class Benefit(models.Model):
    """Benefits are the rewards for the drops."""

    # "d5cdf372-502b-11ef-bafd-0a58a9feac02"
    twitch_id = models.TextField(primary_key=True)

    # When the benefit was first added to the database.
    created_at = models.DateTimeField(null=True, auto_created=True)

    # When the benefit was last modified.
    modified_at = models.DateTimeField(auto_now=True)

    #  Note: This is Twitch's created_at from the API.
    # "2023-11-09T01:18:00.126Z"
    twitch_created_at = models.DateTimeField(null=True)

    # "1"
    entitlement_limit = models.PositiveBigIntegerField(null=True)

    # "https://static-cdn.jtvnw.net/twitch-quests-assets/REWARD/e58ad175-73f6-4392-80b8-fb0223163733.png"
    image_url = models.URLField(blank=True)

    # "True" or "False". None if unknown.
    is_ios_available = models.BooleanField(null=True)

    # "Cosmic Nexus Chimera"
    name = models.TextField(blank=True)

    time_based_drop = models.ForeignKey(
        TimeBasedDrop,
        on_delete=models.CASCADE,
        related_name="benefits",
        null=True,
    )

    class Meta:
        ordering: ClassVar[list[str]] = ["-twitch_created_at"]

    def __str__(self) -> str:
        """Return the name of the benefit and when it was created."""
        return f"{self.name or self.twitch_id} - {self.twitch_created_at}"

    def import_json(self, data: dict, time_based_drop: TimeBasedDrop | None) -> Self:
        """Import the data from the Twitch API."""
        if wrong_typename(data, "DropBenefit"):
            return self

        field_mapping: dict[str, str] = {
            "name": "name",
            "imageAssetURL": "image_url",
            "entitlementLimit": "entitlement_limit",
            "isIOSAvailable": "is_ios_available",
            "createdAt": "twitch_created_at",
        }
        updated: int = update_fields(instance=self, data=data, field_mapping=field_mapping)
        if updated > 0:
            logger.info("Updated %s fields for %s", updated, self)

        if not time_based_drop:
            logger.error("TimeBasedDrop is required for %s", self)
            return self

        if time_based_drop != self.time_based_drop:
            self.time_based_drop = time_based_drop
            logger.info("Updated time based drop %s for %s", time_based_drop, self)
            self.save()

        return self


class RewardCampaign(models.Model):
    """Buy subscriptions to earn rewards."""

    # "dc4ff0b4-4de0-11ef-9ec3-621fb0811846"
    twitch_id = models.TextField(primary_key=True)

    # When the reward campaign was first added to the database.
    created_at = models.DateTimeField(auto_created=True)

    # When the reward campaign was last modified.
    modified_at = models.DateTimeField(auto_now=True)

    # "Buy 1 new sub, get 3 months of Apple TV+"
    name = models.TextField(blank=True)

    # "Apple TV+"
    brand = models.TextField(blank=True)

    # "2024-08-11T11:00:00Z"
    starts_at = models.DateTimeField(null=True)

    # "2024-08-12T05:59:59.999Z"
    ends_at = models.DateTimeField(null=True)

    # "UNKNOWN"
    status = models.TextField(blank=True)

    # "Get 3 months of Apple TV+ with the purchase of a new sub"
    summary = models.TextField(blank=True)

    # "Buy a new sub to get 3 months of Apple TV+"
    instructions = models.TextField(blank=True)

    # ""
    reward_value_url_param = models.TextField(blank=True)

    # "https://tv.apple.com/includes/commerce/redeem/code-entry"
    external_url = models.URLField(blank=True)

    # "https://blog.twitch.tv/2024/07/26/sub-and-get-apple-tv/"
    about_url = models.URLField(blank=True)

    # "True" or "False". None if unknown.
    is_site_wide = models.BooleanField(null=True)

    # "1"
    subs_goal = models.PositiveBigIntegerField(null=True)

    # "0"
    minute_watched_goal = models.PositiveBigIntegerField(null=True)

    # "https://static-cdn.jtvnw.net/twitch-quests-assets/CAMPAIGN/quests_appletv_q3_2024/apple_150x200.png"
    image_url = models.URLField(blank=True)

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="reward_campaigns", null=True)

    scraped_json = models.ForeignKey(
        ScrapedJson,
        null=True,
        on_delete=models.SET_NULL,
        help_text="Reference to the JSON data from the Twitch API.",
    )

    class Meta:
        ordering: ClassVar[list[str]] = ["-starts_at"]

    def __str__(self) -> str:
        """Return the name of the reward campaign and when it was created."""
        return f"{self.name or self.twitch_id} - {self.created_at}"

    def import_json(self, data: dict) -> Self:  # noqa: C901
        """Import the data from the Twitch API."""
        if wrong_typename(data, "RewardCampaign"):
            return self

        field_mapping: dict[str, str] = {
            "name": "name",
            "brand": "brand",
            "startsAt": "starts_at",
            "endsAt": "ends_at",
            "status": "status",
            "summary": "summary",
            "instructions": "instructions",
            "rewardValueURLParam": "reward_value_url_param",  # wtf is this?
            "externalURL": "external_url",
            "aboutURL": "about_url",
            "isSitewide": "is_site_wide",
        }

        updated: int = update_fields(instance=self, data=data, field_mapping=field_mapping)
        if updated > 0:
            logger.info("Updated %s fields for %s", updated, self)

        if data.get("unlockRequirements", {}):
            subs_goal = data["unlockRequirements"].get("subsGoal")
            if subs_goal and subs_goal != self.subs_goal:
                self.subs_goal = subs_goal
                self.save()

            minutes_watched_goal = data["unlockRequirements"].get("minuteWatchedGoal")
            if minutes_watched_goal and minutes_watched_goal != self.minute_watched_goal:
                self.minute_watched_goal = minutes_watched_goal
                self.save()

        image_url = data.get("image", {}).get("image1xURL")
        if image_url and image_url != self.image_url:
            self.image_url = image_url
            self.save()

        if data.get("game") and data["game"].get("id"):
            game_instance, created = Game.objects.update_or_create(twitch_id=data["game"]["id"])
            game_instance.import_json(data["game"], None)
            if created:
                logger.info("Added game %s to %s", game_instance, self)

        if "rewards" in data:
            for reward in data["rewards"]:
                reward_instance, created = Reward.objects.update_or_create(twitch_id=reward["id"])
                reward_instance.import_json(reward, self)
                if created:
                    logger.info("Added reward %s to %s", reward_instance, self)

        return self


class Reward(models.Model):
    """This from the RewardCampaign."""

    # "dc2e9810-4de0-11ef-9ec3-621fb0811846"
    twitch_id = models.TextField(primary_key=True)

    # When the reward was first added to the database.
    created_at = models.DateTimeField(auto_created=True)

    # When the reward was last modified.
    modified_at = models.DateTimeField(auto_now=True)

    # "3 months of Apple TV+"
    name = models.TextField(blank=True)

    # "https://static-cdn.jtvnw.net/twitch-quests-assets/CAMPAIGN/quests_appletv_q3_2024/apple_200x200.png"
    banner_image_url = models.URLField(blank=True)

    # "https://static-cdn.jtvnw.net/twitch-quests-assets/CAMPAIGN/quests_appletv_q3_2024/apple_200x200.png"
    thumbnail_image_url = models.URLField(blank=True)

    # "2024-08-19T19:00:00Z"
    earnable_until = models.DateTimeField(null=True)

    # ""
    redemption_instructions = models.TextField(blank=True)

    # "https://tv.apple.com/includes/commerce/redeem/code-entry"
    redemption_url = models.URLField(blank=True)

    campaign = models.ForeignKey(RewardCampaign, on_delete=models.CASCADE, related_name="rewards", null=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["-earnable_until"]

    def __str__(self) -> str:
        """Return the name of the reward and when it was created."""
        return f"{self.name or self.twitch_id} - {self.created_at}"

    def import_json(self, data: dict, reward_campaign: RewardCampaign | None) -> Self:
        """Import the data from the Twitch API."""
        if wrong_typename(data, "Reward"):
            return self

        field_mapping: dict[str, str] = {
            "name": "name",
            "earnableUntil": "earnable_until",
            "redemptionInstructions": "redemption_instructions",
            "redemptionURL": "redemption_url",
        }

        updated: int = update_fields(instance=self, data=data, field_mapping=field_mapping)
        if updated > 0:
            logger.info("Updated %s fields for %s", updated, self)

        banner_image_url = data.get("bannerImage", {}).get("image1xURL")
        if banner_image_url and banner_image_url != self.banner_image_url:
            self.banner_image_url = banner_image_url
            self.save()

        thumbnail_image_url = data.get("thumbnailImage", {}).get("image1xURL")
        if thumbnail_image_url and thumbnail_image_url != self.thumbnail_image_url:
            self.thumbnail_image_url = thumbnail_image_url
            self.save()

        if reward_campaign and reward_campaign != self.campaign:
            self.campaign = reward_campaign
            self.save()

        return self
