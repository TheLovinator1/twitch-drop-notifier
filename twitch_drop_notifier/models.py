from typing import ClassVar

from django.db import models
from simple_history.models import HistoricalRecords


class Owner(models.Model):
    owner_id = models.UUIDField(
        primary_key=True,
        help_text="The ID of the owner.",
        verbose_name="Owner ID",
        editable=False,
    )
    name = models.TextField(
        help_text="The name of the owner.",
        verbose_name="Developer Name",
    )
    image = models.ImageField(upload_to="images/", blank=True)
    model_created = models.DateTimeField(auto_now_add=True)
    model_updated = models.DateTimeField(auto_now=True)
    history = HistoricalRecords(
        table_name="owner_history",
        excluded_fields=["model_created", "model_updated"],
    )

    class Meta:
        ordering: ClassVar[list[str]] = ["name"]
        verbose_name: str = "Owner"
        db_table: str = "owner"
        db_table_comment: str = "An owner."

    def __str__(self) -> str:
        return self.name


class Game(models.Model):
    game_id = models.TextField(
        help_text="The ID of the game.",
        verbose_name="Game ID",
    )
    display_name = models.TextField(
        help_text="The display name of the game.",
        verbose_name="Game Name",
    )
    slug = models.TextField(
        help_text="The slug of the game.",
        verbose_name="Game Slug",
    )
    image = models.ImageField(upload_to="images/", blank=True)
    model_created = models.DateTimeField(auto_now_add=True)
    model_updated = models.DateTimeField(auto_now=True)
    history = HistoricalRecords(
        table_name="game_history",
        excluded_fields=["model_created", "model_updated"],
    )

    class Meta:
        ordering: ClassVar[list[str]] = ["display_name"]
        verbose_name: str = "Game"
        db_table: str = "game"
        db_table_comment: str = "A game."

    def __str__(self) -> str:
        return f"{self.display_name} (www.twitch.tv/directory/category/{self.slug})"


class Reward(models.Model):
    reward_id = models.UUIDField(
        primary_key=True,
        help_text="The ID of the reward.",
        verbose_name="Reward ID",
        editable=False,
    )
    name = models.TextField(
        help_text="The name of the reward.",
        verbose_name="Reward Name",
    )
    required_minutes_watched = models.IntegerField(
        help_text="The required minutes watched to earn the reward.",
        verbose_name="Required Minutes Watched",
    )
    is_available_on_ios = models.BooleanField(
        default=False,
        help_text="If the reward is available on iOS.",
        verbose_name="Available on iOS",
    )
    image = models.ImageField(upload_to="images/", blank=True)
    start_at = models.DateTimeField(
        help_text="The date and time the reward starts.",
        verbose_name="Start At",
    )
    end_at = models.DateTimeField(
        help_text="The date and time the reward ends.",
        verbose_name="End At",
    )
    created = models.DateTimeField(
        help_text="The date and time the reward was model_created. From Twitch JSON.",
    )

    model_created = models.DateTimeField(
        auto_now_add=True,
        help_text="The date and time the reward was model_created in the database.",
    )
    model_model_updated = models.DateTimeField(auto_now=True)
    history = HistoricalRecords(
        table_name="reward_history",
        excluded_fields=["model_model_created", "model_updated"],
    )

    class Meta:
        ordering: ClassVar[list[str]] = ["name"]
        verbose_name: str = "Reward"
        db_table: str = "reward"
        db_table_comment: str = "A reward."

    def __str__(self) -> str:
        return self.name


class TwitchChannel(models.Model):
    name = models.TextField(
        help_text="The name of the Twitch channel.",
        verbose_name="Twitch Channel Name",
    )
    image = models.ImageField(upload_to="images/", blank=True)
    is_live = models.BooleanField(default=False)
    model_created = models.DateTimeField(auto_now_add=True)
    model_updated = models.DateTimeField(auto_now=True)
    history = HistoricalRecords(
        table_name="twitch_channel_history",
        excluded_fields=["model_created", "model_updated"],
    )

    class Meta:
        ordering: ClassVar[list[str]] = ["name"]
        verbose_name: str = "Twitch Channel"
        db_table: str = "twitch_channel"
        db_table_comment: str = "A Twitch channel."

    def __str__(self) -> str:
        return self.name


class TwitchDrop(models.Model):
    drop_id = models.TextField(
        help_text="The ID of the drop.",
        verbose_name="Drop ID",
    )
    name = models.TextField(
        help_text="The name of the drop.",
        verbose_name="Drop Name",
    )
    description = models.TextField(
        help_text="The description of the drop.",
        verbose_name="Description",
    )
    details_url = models.URLField(
        help_text="The URL to the drop details.",
        verbose_name="Details URL",
    )
    how_to_earn = models.TextField(
        help_text="How to earn the drop.",
        verbose_name="How to Earn",
    )
    image = models.ImageField(upload_to="images/", blank=True)
    start_date = models.DateTimeField(
        help_text="The date and time the drop starts.",
        verbose_name="Start Date",
    )
    end_date = models.DateTimeField(
        help_text="The date and time the drop ends.",
        verbose_name="End Date",
    )
    is_event_based = models.BooleanField(
        default=False,
        help_text="If the drop is event based.",
        verbose_name="Event Based",
    )
    is_time_based = models.BooleanField(
        default=False,
        help_text="If the drop is time based.",
        verbose_name="Time Based",
    )
    reward = models.ForeignKey(
        Reward,
        on_delete=models.CASCADE,
        related_name="twitch_drops",
        verbose_name="Reward",
    )
    account_link_url = models.URLField(
        help_text="The URL to link the Twitch account.",
        verbose_name="Connection",
    )
    participating_channels = models.URLField(
        help_text="The URL to the Twitch stream.",
        verbose_name="Participating Channels",
    )
    status = models.BooleanField(
        default=False,
        help_text="If the drop is active.",
        verbose_name="Status",
    )

    model_created = models.DateTimeField(
        auto_now_add=True,
        editable=False,
        help_text="The date and time the drop was model_created.",
    )
    model_updated = models.DateTimeField(
        auto_now=True,
        help_text="The date and time the drop was last model_updated.",
    )
    history = HistoricalRecords(
        table_name="twitch_drop_history",
        excluded_fields=["model_created", "model_updated"],
    )

    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="twitch_drops",
        verbose_name="Game",
    )
    developer = models.ForeignKey(
        Owner,
        on_delete=models.CASCADE,
        related_name="twitch_drops",
        verbose_name="Developer",
    )

    class Meta:
        ordering: ClassVar[list[str]] = ["name"]
        verbose_name: str = "Twitch Drop"
        db_table: str = "twitch_drop"
        db_table_comment: str = "A Twitch Drop."

    def __str__(self) -> str:
        return f"{self.name} ({self.game.display_name})"
