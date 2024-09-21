from __future__ import annotations

import logging
from datetime import datetime
from io import BytesIO
from typing import TYPE_CHECKING, Any, ClassVar, Literal, Self, cast

import requests
from asgiref.sync import sync_to_async
from django.contrib.auth.models import AbstractUser
from django.core.files import File
from django.core.files.base import ContentFile
from django.db import models
from PIL import Image

if TYPE_CHECKING:
    from django.db.models.fields.files import ImageFieldFile

logger: logging.Logger = logging.getLogger(__name__)

# The image file format to save images as.
image_file_format: Literal["webp"] = "webp"


def wrong_typename(data: dict, expected: str) -> bool:
    """Check if the data is the expected type.

    # TODO(TheLovinator): Double check this.  # noqa: TD003
    Type name examples:
        - Game
        - DropCampaign
        - TimeBasedDrop
        - DropBenefit
        - RewardCampaign
        - Reward

    Args:
        data (dict): The data to check.
        expected (str): The expected type.

    Returns:
        bool: True if the data is not the expected type.
    """
    is_unexpected_type: bool = data.get("__typename", "") != expected
    if is_unexpected_type:
        logger.error("Not a %s? %s", expected, data)

    return is_unexpected_type


def update_field(instance: models.Model, django_field_name: str, new_value: str | datetime | None) -> int:
    """Update a field on an instance if the new value is different from the current value.

    Args:
        instance (models.Model): The Django model instance.
        django_field_name (str): The name of the field to update.
        new_value (str | datetime | None): The new value to update the field with.

    Returns:
        int: If the field was updated, returns 1. Otherwise, returns 0.
    """
    # Get the current value of the field.
    try:
        current_value = getattr(instance, django_field_name)
    except AttributeError:
        logger.exception("Field %s does not exist on %s", django_field_name, instance)
        return 0

    # Only update the field if the new value is different from the current value.
    if new_value and new_value != current_value:
        setattr(instance, django_field_name, new_value)
        return 1

    # 0 fields updated.
    return 0


def get_value(data: dict, key: str) -> datetime | str | None:
    """Get a value from a dictionary.

    We have this function so we can handle values that we need to convert to a different type. For example, we might
    need to convert a string to a datetime object.

    Args:
        data (dict): The dictionary to get the value from.
        key (str): The key to get the value for.

    Returns:
        datetime | str | None: The value from the dictionary
    """
    data_key: Any | None = data.get(key)
    if not data_key:
        return None

    # Dates are in the format "2024-08-12T05:59:59.999Z"
    dates: list[str] = ["endAt", "endsAt,", "startAt", "startsAt", "createdAt", "earnableUntil"]
    if key in dates:
        return datetime.fromisoformat(data_key.replace("Z", "+00:00"))

    return data_key


async def update_fields(instance: models.Model, data: dict, field_mapping: dict[str, str]) -> int:
    """Update multiple fields on an instance using a mapping from external field names to model field names.

    Args:
        instance (models.Model): The Django model instance.
        data (dict): The new data to update the fields with.
        field_mapping (dict[str, str]): A dictionary mapping external field names to model field names.

    Returns:
        int: The number of fields updated. Used for only saving the instance if there were changes.
    """
    dirty = 0
    for json_field, django_field_name in field_mapping.items():
        data_key: datetime | str | None = get_value(data, json_field)
        dirty += update_field(instance=instance, django_field_name=django_field_name, new_value=data_key)

    if dirty > 0:
        await instance.asave()

    return dirty


def convert_image_to_webp(data: bytes | None) -> File | None:
    """Convert an image to a webp format.

    Args:
        data (bytes | None): The image data to convert.

    Returns:
        ImageFile | None: The image converted to a webp format.
    """
    if not data:
        return None

    try:
        with BytesIO(data) as input_buffer, Image.open(input_buffer) as image:
            output_buffer = BytesIO()
            image.save(output_buffer, format=image_file_format)
            output_buffer.seek(0)
            return File(file=Image.open(output_buffer))
    except Exception:
        logger.exception("Failed to convert image to webp.")
        return File(file=Image.open(fp=ContentFile(data)).convert("RGB"))


def fetch_image(image_url: str) -> bytes | None:
    """Fetch an image from a URL and return the response.

    Args:
        image_url (str): The URL of the image to fetch.

    Returns:
        requests.Response | None: The response if the image was fetched, otherwise None.
    """
    response: requests.Response = requests.get(image_url, timeout=5, stream=True)
    response.raise_for_status()

    if response.ok:
        if response.raw:
            logging.debug("Fetched image from %s", image_url)
            return response.raw.read()
        logging.error("Response raw is None for %s", image_url)
        return None
    logging.error("Failed to retrieve content. Status code: %s", response.status_code)
    return None


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

    class Meta:
        ordering: ClassVar[list[str]] = ["name"]

    def __str__(self) -> str:
        return self.name or self.twitch_id

    async def aimport_json(self, data: dict) -> Self:
        if wrong_typename(data, "Organization"):
            return self

        field_mapping: dict[str, str] = {"name": "name"}
        updated: int = await update_fields(instance=self, data=data, field_mapping=field_mapping)
        if updated > 0:
            logger.info("Updated %s fields for %s", updated, self)

        return self


def get_game_image_path(instance: models.Model, filename: str) -> str:
    """Get the path for the game image.

    Args:
        instance (models.Model): The instance of the model. Is a Game.
        filename (str): The filename of the image.

    Returns:
        str: The path to the image.
    """
    instance = cast(Game, instance)

    # Example: game/509658.png
    image_path: str = f"game/{filename}"
    logger.debug("Saved image to %s", image_path)

    return image_path


class Game(models.Model):
    """The game the drop campaign is for. Note that some reward campaigns are not tied to a game."""

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
    image = models.ImageField(null=True, upload_to=get_game_image_path)

    # "halo-infinite"
    slug = models.TextField(null=True, unique=True)

    org = models.ForeignKey(Owner, on_delete=models.CASCADE, related_name="games", null=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["name"]

    def __str__(self) -> str:
        return self.name or self.twitch_id

    def download_image(self) -> ImageFieldFile | None:
        """Download the image for the game.

        Returns:
            ImageFieldFile | None: The image file or None if it doesn't exist.
        """
        # We don't want to re-download the image if it already exists.
        # TODO(TheLovinator): Check if there is a different image available.  # noqa: TD003
        if self.image:
            return self.image

        if not self.box_art_url:
            return None

        response: bytes | None = fetch_image(image_url=self.box_art_url)
        image: File | None = convert_image_to_webp(response)
        if image:
            self.image.save(name=f"{self.twitch_id}.{image_file_format}", content=image, save=True)
            logger.info("Downloaded image for %s to %s", self, self.image.url)

        return None

    async def aimport_json(self, data: dict, owner: Owner | None) -> Self:
        if wrong_typename(data, "Game"):
            return self

        # Map the fields from the JSON data to the Django model fields.
        field_mapping: dict[str, str] = {
            "displayName": "name",
            "boxArtURL": "box_art_url",  # TODO(TheLovinator): Should download the image.  # noqa: TD003
            "slug": "slug",
        }
        updated: int = await update_fields(instance=self, data=data, field_mapping=field_mapping)

        if updated > 0:
            logger.info("Updated %s fields for %s", updated, self)

        # Handle the owner of the game.
        if owner:
            await owner.games.aadd(self)  # type: ignore  # noqa: PGH003
            await self.asave()
            logger.info("Added game %s for %s", self, owner)

        return self


def get_drop_campaign_image_path(instance: models.Model, filename: str) -> str:
    """Get the path for the drop campaign image.

    Args:
        instance (models.Model): The instance of the model. Is a DropCampaign.
        filename (str): The filename of the image.

    Returns:
        str: The path to the image.
    """
    instance = cast(DropCampaign, instance)

    # Example: drop_campaigns/509658/509658.png
    image_path: str = f"drop_campaign/{filename}"
    logger.debug("Saved image to %s", image_path)

    return image_path


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

    image = models.ImageField(null=True, upload_to=get_drop_campaign_image_path)

    # "HCS Open Series - Week 1 - DAY 2 - AUG11"
    name = models.TextField(null=True)

    # "ACTIVE"
    status = models.TextField(null=True)

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="drop_campaigns", null=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["ends_at"]

    def __str__(self) -> str:
        return self.name or self.twitch_id

    def download_image(self) -> ImageFieldFile | None:
        """Download the image for the drop campaign.

        Returns:
            ImageFieldFile | None: The image file or None if it doesn't exist.
        """
        # We don't want to re-download the image if it already exists.
        # TODO(TheLovinator): Check if there is a different image available.  # noqa: TD003
        if self.image:
            return self.image

        if not self.image_url:
            return None

        response: bytes | None = fetch_image(image_url=self.image_url)
        image: File | None = convert_image_to_webp(response)
        if image:
            self.image.save(name=f"{self.twitch_id}.{image_file_format}", content=image, save=True)
            logger.info("Downloaded image for %s to %s", self, self.image.url)

        return None

    async def aimport_json(self, data: dict, game: Game | None, *, scraping_local_files: bool = False) -> Self:
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
            "imageURL": "image_url",  # TODO(TheLovinator): Should download the image.  # noqa: TD003
        }

        updated: int = await update_fields(instance=self, data=data, field_mapping=field_mapping)
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
                await self.asave()

        # Update the game if the game is different or not set.
        if game and await sync_to_async(lambda: game != self.game)():
            self.game = game
            logger.info("Updated game %s for %s", game, self)
            await self.asave()

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

    async def aimport_json(self, data: dict, drop_campaign: DropCampaign | None) -> Self:
        if wrong_typename(data, "TimeBasedDrop"):
            return self

        field_mapping: dict[str, str] = {
            "name": "name",
            "requiredSubs": "required_subs",
            "requiredMinutesWatched": "required_minutes_watched",
            "startAt": "starts_at",
            "endAt": "ends_at",
        }

        updated: int = await update_fields(instance=self, data=data, field_mapping=field_mapping)
        if updated > 0:
            logger.info("Updated %s fields for %s", updated, self)

        if drop_campaign and await sync_to_async(lambda: drop_campaign != self.drop_campaign)():
            self.drop_campaign = drop_campaign
            logger.info("Updated drop campaign %s for %s", drop_campaign, self)
            await self.asave()

        return self


def get_benefit_image_path(instance: models.Model, filename: str) -> str:
    """Get the path for the benefit image.

    Args:
        instance (models.Model): The instance of the model. Is a Benefit.
        filename (str): The filename of the image.

    Returns:
        str: The path to the image.
    """
    instance = cast(Benefit, instance)

    # Example: benefit_images/509658.png
    image_path: str = f"benefit/{filename}"
    logger.debug("Saved image to %s", image_path)

    return image_path


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
    image = models.ImageField(null=True, upload_to=get_benefit_image_path)

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

    def download_image(self) -> ImageFieldFile | None:
        """Download the image for the benefit.

        Returns:
            ImageFieldFile | None: The image file or None if it doesn't exist.
        """
        # TODO(TheLovinator): Check if the image on Twitch is different.  # noqa: TD003
        if self.image:
            logger.debug("Image already exists for %s", self)
            return self.image

        if not self.image_url:
            logger.error("No image URL for %s", self)
            return None

        response: bytes | None = fetch_image(image_url=self.image_url)
        image: File | None = convert_image_to_webp(response)
        if image:
            self.image.save(name=f"{self.twitch_id}.{image_file_format}", content=image, save=True)
            logger.info("Downloaded image for %s to %s", self, self.image.url)

        return None

    async def aimport_json(self, data: dict, time_based_drop: TimeBasedDrop | None) -> Self:
        if wrong_typename(data, "DropBenefit"):
            return self

        field_mapping: dict[str, str] = {
            "name": "name",
            "imageAssetURL": "image_url",  # TODO(TheLovinator): Should download the image.  # noqa: TD003
            "entitlementLimit": "entitlement_limit",
            "isIOSAvailable": "is_ios_available",
            "createdAt": "twitch_created_at",
        }
        updated: int = await update_fields(instance=self, data=data, field_mapping=field_mapping)
        if updated > 0:
            logger.info("Updated %s fields for %s", updated, self)

        if time_based_drop:
            await time_based_drop.benefits.aadd(self)  # type: ignore  # noqa: PGH003
            await time_based_drop.asave()
            logger.info("Added benefit %s for %s", self, time_based_drop)

        return self


def get_reward_image_path(instance: models.Model, filename: str) -> str:
    """Get the path for the reward image.

    Args:
        instance (models.Model): The instance of the model. Is a Reward.
        filename (str): The filename of the image.

    Returns:
        str: The path to the image.
    """
    instance = cast(Reward, instance)

    # Example: reward/509658.png
    image_path: str = f"reward/{filename}"
    logger.debug("Saved image to %s", image_path)

    return image_path


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
    image = models.ImageField(null=True, upload_to=get_reward_image_path)

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="reward_campaigns", null=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["-starts_at"]

    def __str__(self) -> str:
        return self.name or self.twitch_id

    def download_image(self) -> ImageFieldFile | None:
        """Download the image for the drop campaign.

        Returns:
            ImageFieldFile | None: The image file or None if it doesn't exist.
        """
        # We don't want to re-download the image if it already exists.
        # TODO(TheLovinator): Check if there is a different image available.  # noqa: TD003
        if self.image:
            return self.image

        if not self.image_url:
            return None

        response: bytes | None = fetch_image(image_url=self.image_url)
        image: File | None = convert_image_to_webp(response)
        if image:
            file_name: str = f"{self.twitch_id}.{image_file_format}"
            self.image.save(name=file_name, content=image, save=True)
            logger.info("Downloaded image for %s to %s", self, self.image.url)
            return self.image

        return None

    async def aimport_json(self, data: dict) -> Self:
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

        updated: int = await update_fields(instance=self, data=data, field_mapping=field_mapping)
        if updated > 0:
            logger.info("Updated %s fields for %s", updated, self)

        if data.get("unlockRequirements", {}):
            subs_goal = data["unlockRequirements"].get("subsGoal")
            if subs_goal and subs_goal != self.subs_goal:
                self.subs_goal = subs_goal
                await self.asave()

            minutes_watched_goal = data["unlockRequirements"].get("minuteWatchedGoal")
            if minutes_watched_goal and minutes_watched_goal != self.minute_watched_goal:
                self.minute_watched_goal = minutes_watched_goal
                await self.asave()

        image_url = data.get("image", {}).get("image1xURL")
        if image_url and image_url != self.image_url:
            # await sync_to_async(self.download_image)()
            # TODO(TheLovinator): Download the image.  # noqa: TD003
            self.image_url = image_url
            await self.asave()

        if data.get("game") and data["game"].get("id"):
            game, _ = await Game.objects.aget_or_create(twitch_id=data["game"]["id"])
            await game.reward_campaigns.aadd(self)  # type: ignore  # noqa: PGH003
            await self.asave()

        if "rewards" in data:
            for reward in data["rewards"]:
                reward_instance, created = await Reward.objects.aupdate_or_create(twitch_id=reward["id"])
                await reward_instance.aimport_json(reward, self)
                if created:
                    logger.info("Added reward %s to %s", reward_instance, self)

        return self


def get_reward_banner_image_path(instance: models.Model, filename: str) -> str:
    """Get the path for the reward banner image.

    Args:
        instance (models.Model): The instance of the model. Is a Reward.
        filename (str): The filename of the image.

    Returns:
        str: The path to the image.
    """
    instance = cast(Reward, instance)

    # Example: reward/banner_509658.png
    image_path: str = f"reward/banner_{filename}"
    logger.debug("Saved image to %s", image_path)

    return image_path


def get_reward_thumbnail_image_path(instance: models.Model, filename: str) -> str:
    """Get the path for the reward thumbnail image.

    Args:
        instance (models.Model): The instance of the model. Is a Reward.
        filename (str): The filename of the image.

    Returns:
        str: The path to the image.
    """
    instance = cast(Reward, instance)

    # Example: reward/thumb_509658.png
    image_path: str = f"reward/thumb_{filename}"
    logger.debug("Saved image to %s", image_path)

    return image_path


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
    banner_image = models.ImageField(null=True, upload_to=get_reward_banner_image_path)

    # "https://static-cdn.jtvnw.net/twitch-quests-assets/CAMPAIGN/quests_appletv_q3_2024/apple_200x200.png"
    thumbnail_image_url = models.URLField(null=True)
    thumbnail_image = models.ImageField(null=True, upload_to=get_reward_thumbnail_image_path)

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

    def download_banner_image(self) -> ImageFieldFile | None:
        """Download the banner image for the reward.

        Returns:
            ImageFieldFile | None: The image file or None if it doesn't exist.
        """
        # We don't want to re-download the image if it already exists.
        # TODO(TheLovinator): Check if there is a different image available.  # noqa: TD003
        if self.banner_image:
            return self.banner_image

        if not self.banner_image_url:
            return None

        if not self.banner_image and self.banner_image_url:
            response: bytes | None = fetch_image(image_url=self.banner_image_url)
            image: File | None = convert_image_to_webp(response)
            if image:
                self.banner_image.save(name=f"{self.twitch_id}.{image_file_format}", content=image, save=True)
                logger.info("Downloaded image for %s to %s", self, self.banner_image.url)

        return None

    def download_thumbnail_image(self) -> ImageFieldFile | None:
        """Download the thumbnail image for the reward.

        Returns:
            ImageFieldFile | None: The image file or None if it doesn't exist.
        """
        # We don't want to re-download the image if it already exists.
        # TODO(TheLovinator): Check if there is a different image available.  # noqa: TD003
        if self.thumbnail_image:
            return self.thumbnail_image

        if not self.thumbnail_image_url:
            return None

        if not self.thumbnail_image and self.thumbnail_image_url:
            response: bytes | None = fetch_image(image_url=self.thumbnail_image_url)
            image: File | None = convert_image_to_webp(response)
            if image:
                self.thumbnail_image.save(name=f"{self.twitch_id}.{image_file_format}", content=image, save=True)
                logger.info("Downloaded image for %s to %s", self, self.thumbnail_image.url)

        return None

    async def aimport_json(self, data: dict, reward_campaign: RewardCampaign | None) -> Self:
        if wrong_typename(data, "Reward"):
            return self

        field_mapping: dict[str, str] = {
            "name": "name",
            "earnableUntil": "earnable_until",
            "redemptionInstructions": "redemption_instructions",
            "redemptionURL": "redemption_url",
        }

        updated: int = await update_fields(instance=self, data=data, field_mapping=field_mapping)
        if updated > 0:
            logger.info("Updated %s fields for %s", updated, self)

        banner_image_url = data.get("bannerImage", {}).get("image1xURL")
        if banner_image_url:
            await sync_to_async(self.download_banner_image)()
            if banner_image_url != self.banner_image_url:
                self.banner_image_url = banner_image_url
                await self.asave()

        thumbnail_image_url = data.get("thumbnailImage", {}).get("image1xURL")
        if thumbnail_image_url:
            await sync_to_async(self.download_thumbnail_image)()
            if thumbnail_image_url != self.thumbnail_image_url:
                self.thumbnail_image_url = thumbnail_image_url
                await self.asave()

        if reward_campaign and await sync_to_async(lambda: reward_campaign != self.campaign)():
            self.campaign = reward_campaign
            await self.asave()

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
