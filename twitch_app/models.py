import auto_prefetch
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.db import models
from django.db.models import Value
from django.db.models.functions import (
    Concat,
)
from django.utils import timezone
from simple_history.models import HistoricalRecords


class Organization(auto_prefetch.Model):
    id = models.TextField(primary_key=True)
    name = models.TextField(blank=True, null=True)
    added_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    modified_at = models.DateTimeField(blank=True, null=True, auto_now=True)

    class Meta(auto_prefetch.Model.Meta):
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name or self.id


class Game(auto_prefetch.Model):
    id = models.TextField(primary_key=True)
    slug = models.TextField(blank=True, null=True)
    twitch_url = models.GeneratedField(  # type: ignore  # noqa: PGH003
        expression=Concat(Value("https://www.twitch.tv/directory/category/"), "slug"),
        output_field=models.TextField(),
        db_persist=True,
    )
    image_url = models.GeneratedField(  # type: ignore  # noqa: PGH003
        expression=Concat(
            Value("https://static-cdn.jtvnw.net/ttv-boxart/"),
            "id",
            Value("_IGDB.jpg"),
        ),
        output_field=models.URLField(),
        db_persist=True,
    )
    display_name = models.TextField(blank=True, null=True)
    added_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    modified_at = models.DateTimeField(blank=True, null=True, auto_now=True)
    history = HistoricalRecords()

    class Meta(auto_prefetch.Model.Meta):
        verbose_name = "Game"
        verbose_name_plural = "Games"
        ordering = ("display_name",)

    def __str__(self) -> str:
        return self.display_name or self.slug or self.id


class DropBenefit(auto_prefetch.Model):
    id = models.TextField(primary_key=True)
    created_at = models.DateTimeField(blank=True, null=True)
    entitlement_limit = models.IntegerField(blank=True, null=True)
    image_asset_url = models.URLField(blank=True, null=True)
    is_ios_available = models.BooleanField(blank=True, null=True)
    name = models.TextField(blank=True, null=True)
    owner_organization = auto_prefetch.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
    )
    game = auto_prefetch.ForeignKey(Game, on_delete=models.CASCADE)
    added_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    modified_at = models.DateTimeField(blank=True, null=True, auto_now=True)
    history = HistoricalRecords()

    class Meta(auto_prefetch.Model.Meta):
        verbose_name = "Drop Benefit"
        verbose_name_plural = "Drop Benefits"
        ordering = ("name",)

    def __str__(self) -> str:
        return f"{self.owner_organization.name} - {self.game.display_name} - {self.name}"


class TimeBasedDrop(auto_prefetch.Model):
    id = models.TextField(primary_key=True)
    required_subs = models.IntegerField(blank=True, null=True)
    end_at = models.DateTimeField(blank=True, null=True)
    name = models.TextField(blank=True, null=True)
    required_minutes_watched = models.IntegerField(blank=True, null=True)
    start_at = models.DateTimeField(blank=True, null=True)
    benefits = models.ManyToManyField(DropBenefit)
    added_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    modified_at = models.DateTimeField(blank=True, null=True, auto_now=True)
    history = HistoricalRecords()

    class Meta(auto_prefetch.Model.Meta):
        verbose_name = "Time-Based Drop"
        verbose_name_plural = "Time-Based Drops"
        ordering = ("name",)

    def __str__(self) -> str:
        if self.end_at:
            if self.end_at < timezone.now():
                return f"{self.benefits.first()} - {self.name} - Ended {naturaltime(self.end_at)}"
            return f"{self.benefits.first()} - {self.name} - Ends in {naturaltime(self.end_at)}"
        return f"{self.benefits.first()} - {self.name}"


class DropCampaign(auto_prefetch.Model):
    id = models.TextField(primary_key=True)
    account_link_url = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    details_url = models.URLField(blank=True, null=True)
    end_at = models.DateTimeField(blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    name = models.TextField(blank=True, null=True)
    start_at = models.DateTimeField(blank=True, null=True)
    status = models.TextField(blank=True, null=True)
    game = auto_prefetch.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="drop_campaigns",
    )
    owner = auto_prefetch.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="drop_campaigns",
    )
    time_based_drops = models.ManyToManyField(TimeBasedDrop)
    added_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    modified_at = models.DateTimeField(blank=True, null=True, auto_now=True)
    history = HistoricalRecords()

    class Meta(auto_prefetch.Model.Meta):
        verbose_name = "Drop Campaign"
        verbose_name_plural = "Drop Campaigns"
        ordering = ("name",)

    def __str__(self) -> str:
        return f"{self.owner.name} - {self.game.display_name} - {self.name}"
