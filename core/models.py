from __future__ import annotations

import logging

from django.contrib.auth.models import AbstractUser
from django.db import models

logger: logging.Logger = logging.getLogger(__name__)


class Owner(models.Model):
    """The company or person that owns the game.

    Drops will be grouped by the owner. Users can also subscribe to owners.
    """

    id = models.TextField(primary_key=True)  # "ad299ac0-f1a5-417d-881d-952c9aed00e9"
    name = models.TextField(null=True)  # "Microsoft"

    def __str__(self) -> str:
        return self.name or "Owner name unknown"


class Game(models.Model):
    """This is the game we will see on the front end."""

    twitch_id = models.TextField(primary_key=True)  # "509658"

    # "https://www.twitch.tv/directory/category/halo-infinite"
    game_url = models.URLField(null=True, default="https://www.twitch.tv/")
    name = models.TextField(null=True, default="Game name unknown")  # "Halo Infinite"

    # "https://static-cdn.jtvnw.net/ttv-boxart/Halo%20Infinite.jpg"
    box_art_url = models.URLField(null=True, default="https://static-cdn.jtvnw.net/ttv-static/404_boxart.jpg")
    slug = models.TextField(null=True)  # "halo-infinite"

    org = models.ForeignKey(Owner, on_delete=models.CASCADE, related_name="games", null=True)

    def __str__(self) -> str:
        return self.name or "Game name unknown"


class DropCampaign(models.Model):
    """This is the drop campaign we will see on the front end."""

    id = models.TextField(primary_key=True)  # "f257ce6e-502a-11ef-816e-0a58a9feac02"
    created_at = models.DateTimeField(null=True, auto_created=True)  # "2024-08-11T00:00:00Z"
    modified_at = models.DateTimeField(null=True, auto_now=True)  # "2024-08-12T00:00:00Z"

    account_link_url = models.URLField(null=True)  # "https://www.halowaypoint.com/settings/linked-accounts"

    # "Tune into this HCS Grassroots event to earn Halo Infinite in-game content!"
    description = models.TextField(null=True)
    details_url = models.URLField(null=True)  # "https://www.halowaypoint.com"

    ends_at = models.DateTimeField(null=True)  # "2024-08-12T05:59:59.999Z"
    starts_at = models.DateTimeField(null=True)  # "2024-08-11T11:00:00Z""

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="drop_campaigns", null=True)

    # "https://static-cdn.jtvnw.net/twitch-quests-assets/CAMPAIGN/c8e02666-8b86-471f-bf38-7ece29a758e4.png"
    image_url = models.URLField(null=True)

    name = models.TextField(null=True)  # "HCS Open Series - Week 1 - DAY 2 - AUG11"
    status = models.TextField(null=True)  # "ACTIVE"

    def __str__(self) -> str:
        return self.name or "Drop campaign name unknown"


class Channel(models.Model):
    """This is the channel we will see on the front end."""

    twitch_id = models.TextField(primary_key=True)  # "222719079"
    display_name = models.TextField(null=True, default="Channel name unknown")  # "LVTHalo"
    name = models.TextField(null=True)  # "lvthalo"
    twitch_url = models.URLField(null=True, default="https://www.twitch.tv/")  # "https://www.twitch.tv/lvthalo"
    live = models.BooleanField(default=False)  # "True"

    drop_campaigns = models.ManyToManyField(DropCampaign, related_name="channels")

    def __str__(self) -> str:
        return self.display_name or "Channel name unknown"


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


class Benefit(models.Model):
    """This is the benefit we will see on the front end."""

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


class User(AbstractUser):
    """Extended User model to include subscriptions."""

    subscribed_games = models.ManyToManyField(
        "Game",
        through="GameSubscription",
        related_name="subscribed_users",
        blank=True,
    )
    subscribed_owners = models.ManyToManyField(
        "Owner",
        through="OwnerSubscription",
        related_name="subscribed_users",
        blank=True,
    )
    subscribe_to_news = models.BooleanField(default=False, help_text="Subscribe to news")
    subscribe_to_new_games = models.BooleanField(default=False, help_text="Subscribe to new games")

    def __str__(self) -> str:
        return self.username


class DiscordWebhook(models.Model):
    """A Discord webhook for sending notifications."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="discord_webhooks")
    url = models.URLField()
    name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return f"{self.name} ({self.user.username})"


class GameSubscription(models.Model):
    """A subscription to a specific game with a chosen webhook."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    webhook = models.ForeignKey(DiscordWebhook, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("user", "game")

    def __str__(self) -> str:
        return f"{self.user.username} -> {self.game.name} via {self.webhook.name}"


class OwnerSubscription(models.Model):
    """A subscription to a specific owner with a chosen webhook."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE)
    webhook = models.ForeignKey(DiscordWebhook, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("user", "owner")

    def __str__(self) -> str:
        return f"{self.user.username} -> {self.owner.name} via {self.webhook.name}"
