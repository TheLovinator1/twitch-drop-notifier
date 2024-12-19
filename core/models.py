from __future__ import annotations

import logging
from typing import TYPE_CHECKING, ClassVar, Self

import auto_prefetch
from django.contrib.auth.models import AbstractUser
from django.db import models

from core.models_utils import update_fields, wrong_typename

if TYPE_CHECKING:
    from django.db.models import Index

logger: logging.Logger = logging.getLogger(__name__)


class User(AbstractUser):
    """Custom user model."""

    class Meta:
        ordering: ClassVar[list[str]] = ["username"]

    def __str__(self) -> str:
        """Return the username."""
        return self.username


class ScrapedJson(auto_prefetch.Model):
    """The JSON data from the Twitch API.

    This data is from https://github.com/TheLovinator1/TwitchDropsMiner.
    """

    json_data = models.JSONField(unique=True, help_text="The JSON data from the Twitch API.")
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    imported_at = models.DateTimeField(null=True)

    class Meta(auto_prefetch.Model.Meta):
        ordering: ClassVar[list[str]] = ["-created_at"]

    def __str__(self) -> str:
        """Return the created at date and optionally if not imported yet."""
        return f"{'' if self.imported_at else 'Not imported - '}{self.created_at}"


class Owner(auto_prefetch.Model):
    """The company or person that owns the game.

    Drops will be grouped by the owner. Users can also subscribe to owners.

    JSON:
        {
            "data": {
                "user": {
                    "dropCampaign": {
                        "owner": {
                            "id": "36c4e21d-bdf3-410c-97c3-5a5a4bf1399b",
                            "name": "The Pok\u00e9mon Company",
                            "__typename": "Organization"
                        }
                    }
                }
            }
        }
    """

    # Django fields
    # Example: "36c4e21d-bdf3-410c-97c3-5a5a4bf1399b"
    twitch_id = models.TextField(primary_key=True, help_text="The Twitch ID of the owner.")
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    # Twitch fields
    # Example: "The Pokémon Company"
    name = models.TextField(blank=True, help_text="The name of the owner.")

    class Meta(auto_prefetch.Model.Meta):
        ordering: ClassVar[list[str]] = ["name"]
        indexes: ClassVar[list[Index]] = [
            models.Index(fields=["name"], name="owner_name_idx"),
            models.Index(fields=["created_at"], name="owner_created_at_idx"),
        ]

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


class Game(auto_prefetch.Model):
    """The game the drop campaign is for. Note that some reward campaigns are not tied to a game.

    JSON:
        "game": {
            "id": "155409827",
            "slug": "pokemon-trading-card-game-live",
            "displayName": "Pok\u00e9mon Trading Card Game Live",
            "__typename": "Game"
        }


    Secondary JSON:
        "game": {
            "id": "155409827",
            "displayName": "Pok\u00e9mon Trading Card Game Live",
            "boxArtURL": "https://static-cdn.jtvnw.net/ttv-boxart/155409827_IGDB-120x160.jpg",
            "__typename": "Game"
        }


    Tertiary JSON:
        "game": {
            "id": "155409827",
            "name": "Pok\u00e9mon Trading Card Game Live",
            "__typename": "Game"
        }

    """

    # Django fields
    # "155409827"
    twitch_id = models.TextField(primary_key=True, help_text="The Twitch ID of the game.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="When the game was first added to the database.")
    modified_at = models.DateTimeField(auto_now=True, help_text="When the game was last modified.")

    # Twitch fields
    # "https://www.twitch.tv/directory/category/pokemon-trading-card-game-live"
    # This is created when the game is created.
    game_url = models.URLField(blank=True, help_text="The URL to the game on Twitch.")

    # "Pokémon Trading Card Game Live"
    display_name = models.TextField(blank=True, help_text="The display name of the game.")

    # "Pokémon Trading Card Game Live"
    name = models.TextField(blank=True, help_text="The name of the game.")

    # "https://static-cdn.jtvnw.net/ttv-boxart/155409827_IGDB-120x160.jpg"
    box_art_url = models.URLField(blank=True, help_text="URL to the box art of the game.")

    # "pokemon-trading-card-game-live"
    slug = models.TextField(blank=True)

    # The owner of the game.
    # This is optional because some games are not tied to an owner.
    org = auto_prefetch.ForeignKey(Owner, on_delete=models.CASCADE, related_name="games", null=True)

    class Meta(auto_prefetch.Model.Meta):
        ordering: ClassVar[list[str]] = ["display_name"]
        indexes: ClassVar[list[Index]] = [
            models.Index(fields=["display_name"], name="game_display_name_idx"),
            models.Index(fields=["name"], name="game_name_idx"),
            models.Index(fields=["created_at"], name="game_created_at_idx"),
        ]

    def __str__(self) -> str:
        """Return the name of the game and when it was created."""
        return f"{self.display_name or self.twitch_id} - {self.created_at}"

    def import_json(self, data: dict, owner: Owner | None) -> Self:
        """Import the data from the Twitch API."""
        if wrong_typename(data, "Game"):
            return self

        if not owner:
            logger.error("Owner is required for %s: %s", self, data)
            return self

        # Map the fields from the JSON data to the Django model fields.
        field_mapping: dict[str, str] = {
            "displayName": "display_name",
            "name": "name",
            "boxArtURL": "box_art_url",
            "slug": "slug",
        }
        updated: int = update_fields(instance=self, data=data, field_mapping=field_mapping)

        if updated > 0:
            logger.info("Updated %s fields for %s", updated, self)

        # Update the owner if the owner is different or not set.
        if owner != self.org:
            self.org = owner
            logger.info("Updated owner %s for %s", owner, self)

        self.game_url = f"https://www.twitch.tv/directory/category/{self.slug}"

        self.save()

        return self


class DropCampaign(auto_prefetch.Model):
    """This is the drop campaign we will see on the front end."""

    # Django fields
    # "f257ce6e-502a-11ef-816e-0a58a9feac02"
    twitch_id = models.TextField(primary_key=True, help_text="The Twitch ID of the drop campaign.")
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the drop campaign was first added to the database.",
    )
    modified_at = models.DateTimeField(auto_now=True, help_text="When the drop campaign was last modified.")

    # Twitch fields
    # "https://www.halowaypoint.com/settings/linked-accounts"
    account_link_url = models.URLField(blank=True, help_text="The URL to link accounts for the drop campaign.")

    # "Tune into this HCS Grassroots event to earn Halo Infinite in-game content!"
    description = models.TextField(blank=True, help_text="The description of the drop campaign.")

    # "https://www.halowaypoint.com"
    details_url = models.URLField(blank=True, help_text="The URL to the details of the drop campaign.")

    # "2024-08-12T05:59:59.999Z"
    ends_at = models.DateTimeField(null=True, help_text="When the drop campaign ends.")

    # "2024-08-11T11:00:00Z""
    starts_at = models.DateTimeField(null=True, help_text="When the drop campaign starts.")

    # "https://static-cdn.jtvnw.net/twitch-quests-assets/CAMPAIGN/c8e02666-8b86-471f-bf38-7ece29a758e4.png"
    image_url = models.URLField(blank=True, help_text="The URL to the image for the drop campaign.")

    # "HCS Open Series - Week 1 - DAY 2 - AUG11"
    name = models.TextField(blank=True, help_text="The name of the drop campaign.")

    # "ACTIVE"
    status = models.TextField(blank=True, help_text="The status of the drop campaign.")

    # The game this drop campaign is for.
    game = auto_prefetch.ForeignKey(to=Game, on_delete=models.CASCADE, related_name="drop_campaigns", null=True)

    # The JSON data from the Twitch API.
    # We use this to find out where the game came from.
    scraped_json = auto_prefetch.ForeignKey(
        to=ScrapedJson,
        null=True,
        on_delete=models.SET_NULL,
        help_text="Reference to the JSON data from the Twitch API.",
    )

    class Meta(auto_prefetch.Model.Meta):
        ordering: ClassVar[list[str]] = ["ends_at"]
        indexes: ClassVar[list[Index]] = [
            models.Index(fields=["name"], name="drop_campaign_name_idx"),
            models.Index(fields=["starts_at"], name="drop_campaign_starts_at_idx"),
            models.Index(fields=["ends_at"], name="drop_campaign_ends_at_idx"),
        ]

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

        if not scraping_local_files:
            status = data.get("status")
            if status and status != self.status:
                self.status = status
                self.save()

        # Update the game if the game is different or not set.
        if game and game != self.game:
            self.game = game
            logger.info("Updated game %s for %s", game, self)
            self.save()

        return self


class TimeBasedDrop(auto_prefetch.Model):
    """This is the drop we will see on the front end.

    JSON:
        {
            "id": "bd663e10-b297-11ef-a6a3-0a58a9feac02",
            "requiredSubs": 0,
            "benefitEdges": [
                {
                    "benefit": {
                        "id": "f751ba67-7c8b-4c41-b6df-bcea0914f3ad_CUSTOM_ID_EnergisingBoltFlaskEffect",
                        "createdAt": "2024-12-04T23:25:50.995Z",
                        "entitlementLimit": 1,
                        "game": {
                            "id": "1702520304",
                            "name": "Path of Exile 2",
                            "__typename": "Game"
                        },
                        "imageAssetURL": "https://static-cdn.jtvnw.net/twitch-quests-assets/REWARD/d70e4e75-7237-4730-9a10-b6016aaaa795.png",
                        "isIosAvailable": false,
                        "name": "Energising Bolt Flask",
                        "ownerOrganization": {
                            "id": "f751ba67-7c8b-4c41-b6df-bcea0914f3ad",
                            "name": "Grinding Gear Games",
                            "__typename": "Organization"
                        },
                        "distributionType": "DIRECT_ENTITLEMENT",
                        "__typename": "DropBenefit"
                    },
                    "entitlementLimit": 1,
                    "__typename": "DropBenefitEdge"
                }
            ],
            "endAt": "2024-12-14T07:59:59.996Z",
            "name": "Early Access Bundle",
            "preconditionDrops": null,
            "requiredMinutesWatched": 180,
            "startAt": "2024-12-06T19:00:00Z",
            "__typename": "TimeBasedDrop"
        }
    """

    # Django fields
    # "d5cdf372-502b-11ef-bafd-0a58a9feac02"
    twitch_id = models.TextField(primary_key=True, help_text="The Twitch ID of the drop.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="When the drop was first added to the database.")
    modified_at = models.DateTimeField(auto_now=True, help_text="When the drop was last modified.")

    # Twitch fields
    # "1"
    required_subs = models.PositiveBigIntegerField(null=True, help_text="The number of subs required for the drop.")

    # "2024-08-12T05:59:59.999Z"
    ends_at = models.DateTimeField(null=True, help_text="When the drop ends.")

    # "Cosmic Nexus Chimera"
    name = models.TextField(blank=True, help_text="The name of the drop.")

    # "120"
    required_minutes_watched = models.PositiveBigIntegerField(
        null=True,
        help_text="The number of minutes watched required.",
    )

    # "2024-08-11T11:00:00Z"
    starts_at = models.DateTimeField(null=True, help_text="When the drop starts.")

    # The drop campaign this drop is part of.
    drop_campaign = auto_prefetch.ForeignKey(
        DropCampaign,
        on_delete=models.CASCADE,
        related_name="drops",
        null=True,
        help_text="The drop campaign this drop is part of.",
    )

    class Meta(auto_prefetch.Model.Meta):
        ordering: ClassVar[list[str]] = ["required_minutes_watched"]
        indexes: ClassVar[list[Index]] = [
            models.Index(fields=["name"], name="time_based_drop_name_idx"),
            models.Index(fields=["starts_at"], name="time_based_drop_starts_at_idx"),
            models.Index(fields=["ends_at"], name="time_based_drop_ends_at_idx"),
        ]

    def __str__(self) -> str:
        """Return the name of the drop and when it was created."""
        return f"{self.name or self.twitch_id} - {self.created_at}"

    def import_json(self, data: dict, drop_campaign: DropCampaign | None) -> Self:
        """Import the data from the Twitch API."""
        if wrong_typename(data, "TimeBasedDrop"):
            return self

        # preconditionDrops is null in the JSON. We probably should use it when we know what it is.
        if data.get("preconditionDrops"):
            logger.error("preconditionDrops is not None for %s", self)

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


class Benefit(auto_prefetch.Model):
    """Benefits are the rewards for the drops."""

    # Django fields
    # "d5cdf372-502b-11ef-bafd-0a58a9feac02"
    twitch_id = models.TextField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    # Twitch fields
    # Note: This is Twitch's created_at from the API and not our created_at.
    # "2023-11-09T01:18:00.126Z"
    twitch_created_at = models.DateTimeField(null=True, help_text="When the benefit was created on Twitch.")

    # "1"
    entitlement_limit = models.PositiveBigIntegerField(
        null=True,
        help_text="The number of times the benefit can be claimed.",
    )

    # "https://static-cdn.jtvnw.net/twitch-quests-assets/REWARD/e58ad175-73f6-4392-80b8-fb0223163733.png"
    image_asset_url = models.URLField(blank=True, help_text="The URL to the image for the benefit.")

    # "True" or "False". None if unknown.
    is_ios_available = models.BooleanField(null=True, help_text="If the benefit is farmable on iOS.")

    # "Cosmic Nexus Chimera"
    name = models.TextField(blank=True, help_text="The name of the benefit.")

    # The game this benefit is for.
    time_based_drop = auto_prefetch.ForeignKey(
        TimeBasedDrop,
        on_delete=models.CASCADE,
        related_name="benefits",
        null=True,
        help_text="The time based drop this benefit is for.",
    )

    # The game this benefit is for.
    game = auto_prefetch.ForeignKey(Game, on_delete=models.CASCADE, related_name="benefits", null=True)

    # The owner of the benefit.
    owner_organization = auto_prefetch.ForeignKey(Owner, on_delete=models.CASCADE, related_name="benefits", null=True)

    # Distribution type.
    # "DIRECT_ENTITLEMENT"
    distribution_type = models.TextField(blank=True, help_text="The distribution type of the benefit.")

    class Meta(auto_prefetch.Model.Meta):
        ordering: ClassVar[list[str]] = ["-twitch_created_at"]
        indexes: ClassVar[list[Index]] = [
            models.Index(fields=["name"], name="benefit_name_idx"),
            models.Index(fields=["twitch_created_at"], name="benefit_twitch_created_at_idx"),
            models.Index(fields=["created_at"], name="benefit_created_at_idx"),
            models.Index(fields=["is_ios_available"], name="benefit_is_ios_available_idx"),
        ]

    def __str__(self) -> str:
        """Return the name of the benefit and when it was created."""
        return f"{self.name or self.twitch_id} - {self.twitch_created_at}"

    def import_json(self, data: dict, time_based_drop: TimeBasedDrop | None) -> Self:
        """Import the data from the Twitch API."""
        if wrong_typename(data, "DropBenefit"):
            return self

        field_mapping: dict[str, str] = {
            "name": "name",
            "imageAssetURL": "image_asset_url",
            "entitlementLimit": "entitlement_limit",
            "isIosAvailable": "is_ios_available",
            "createdAt": "twitch_created_at",
            "distributionType": "distribution_type",
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

        if data.get("game") and data["game"].get("id"):
            game_instance, created = Game.objects.update_or_create(twitch_id=data["game"]["id"])
            game_instance.import_json(data["game"], None)
            if created:
                logger.info("Added game %s to %s", game_instance, self)

        if data.get("ownerOrganization") and data["ownerOrganization"].get("id"):
            owner_instance, created = Owner.objects.update_or_create(twitch_id=data["ownerOrganization"]["id"])
            owner_instance.import_json(data["ownerOrganization"])
            if created:
                logger.info("Added owner %s to %s", owner_instance, self)

        return self
