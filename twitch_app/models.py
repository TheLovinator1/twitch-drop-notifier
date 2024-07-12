from typing import Literal

import auto_prefetch
from django.db import models
from django.db.models import Value
from django.db.models.functions import Concat


class Organization(auto_prefetch.Model):
    """The company that owns the game.

    For example, 2K games.
    """

    id = models.TextField(primary_key=True)
    name = models.TextField(blank=True, null=True)
    added_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    modified_at = models.DateTimeField(blank=True, null=True, auto_now=True)

    class Meta(auto_prefetch.Model.Meta):
        verbose_name: str = "Organization"
        verbose_name_plural: str = "Organizations"
        ordering: tuple[Literal["name"]] = ("name",)

    def __str__(self) -> str:
        return self.name or self.id


class Game(auto_prefetch.Model):
    """The game that the drop campaign is for.

    For example, MultiVersus.
    """

    organization = auto_prefetch.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="games",
    )
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

    class Meta(auto_prefetch.Model.Meta):
        verbose_name: str = "Game"
        verbose_name_plural: str = "Games"
        ordering: tuple[Literal["display_name"]] = ("display_name",)

    def __str__(self) -> str:
        return self.display_name or self.slug or self.id


class Drop(auto_prefetch.Model):
    """The actual drop that is being given out."""

    id = models.TextField(primary_key=True)
    created_at = models.DateTimeField(blank=True, null=True)
    entitlement_limit = models.IntegerField(blank=True, null=True)
    image_asset_url = models.URLField(blank=True, null=True)
    name = models.TextField(blank=True, null=True)
    added_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    modified_at = models.DateTimeField(blank=True, null=True, auto_now=True)
    required_subs = models.IntegerField(blank=True, null=True)
    end_at = models.DateTimeField(blank=True, null=True)
    required_minutes_watched = models.IntegerField(blank=True, null=True)
    start_at = models.DateTimeField(blank=True, null=True)
    drop_campaign = auto_prefetch.ForeignKey("DropCampaign", on_delete=models.CASCADE, related_name="drops")

    class Meta(auto_prefetch.Model.Meta):
        verbose_name: str = "Drop"
        verbose_name_plural: str = "Drops"
        ordering: tuple[Literal["name"]] = ("name",)

    def __str__(self) -> str:
        return f"{self.name}"


class DropCampaign(auto_prefetch.Model):
    """Drops are grouped into campaigns.

    For example, MultiVersus S1 Drops
    """

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
    added_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    modified_at = models.DateTimeField(blank=True, null=True, auto_now=True)

    class Meta(auto_prefetch.Model.Meta):
        verbose_name: str = "Drop Campaign"
        verbose_name_plural: str = "Drop Campaigns"
        ordering: tuple[Literal["name"]] = ("name",)

    def __str__(self) -> str:
        return f"{self.game.display_name} - {self.name}"
