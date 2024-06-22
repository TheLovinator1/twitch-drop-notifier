from django.db import models
from django.db.models import Value
from django.db.models.functions import (
    Concat,
)


class Organization(models.Model):
    id = models.TextField(primary_key=True)
    name = models.TextField(blank=True, null=True)
    added_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    modified_at = models.DateTimeField(blank=True, null=True, auto_now=True)

    def __str__(self) -> str:
        return self.name or self.id


class Game(models.Model):
    id = models.TextField(primary_key=True)
    slug = models.TextField(blank=True, null=True)
    twitch_url = models.GeneratedField(  # type: ignore  # noqa: PGH003
        expression=Concat(Value("https://www.twitch.tv/directory/category/"), "slug"),
        output_field=models.TextField(),
        db_persist=True,
    )
    display_name = models.TextField(blank=True, null=True)
    added_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    modified_at = models.DateTimeField(blank=True, null=True, auto_now=True)

    def __str__(self) -> str:
        return self.display_name or self.slug or self.id


class Channel(models.Model):
    id = models.TextField(primary_key=True)
    display_name = models.TextField(blank=True, null=True)
    name = models.TextField(blank=True, null=True)
    added_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    modified_at = models.DateTimeField(blank=True, null=True, auto_now=True)

    def __str__(self) -> str:
        return self.display_name or self.name or self.id


class DropBenefit(models.Model):
    id = models.TextField(primary_key=True)
    created_at = models.DateTimeField(blank=True, null=True)
    entitlement_limit = models.IntegerField(blank=True, null=True)
    image_asset_url = models.URLField(blank=True, null=True)
    is_ios_available = models.BooleanField(blank=True, null=True)
    name = models.TextField(blank=True, null=True)
    owner_organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    added_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    modified_at = models.DateTimeField(blank=True, null=True, auto_now=True)

    def __str__(self) -> str:
        return self.name or self.id


class TimeBasedDrop(models.Model):
    id = models.TextField(primary_key=True)
    required_subs = models.IntegerField(blank=True, null=True)
    end_at = models.DateTimeField(blank=True, null=True)
    name = models.TextField(blank=True, null=True)
    required_minutes_watched = models.IntegerField(blank=True, null=True)
    start_at = models.DateTimeField(blank=True, null=True)
    benefits = models.ManyToManyField(DropBenefit)
    added_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    modified_at = models.DateTimeField(blank=True, null=True, auto_now=True)

    def __str__(self) -> str:
        return self.name or self.id


class DropCampaign(models.Model):
    id = models.TextField(primary_key=True)
    account_link_url = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    details_url = models.URLField(blank=True, null=True)
    end_at = models.DateTimeField(blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    name = models.TextField(blank=True, null=True)
    start_at = models.DateTimeField(blank=True, null=True)
    status = models.TextField(blank=True, null=True)
    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="drop_campaigns",
    )
    owner = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="drop_campaigns",
    )
    channels = models.ManyToManyField(Channel)
    time_based_drops = models.ManyToManyField(TimeBasedDrop)
    added_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    modified_at = models.DateTimeField(blank=True, null=True, auto_now=True)

    def __str__(self) -> str:
        return self.name or self.id


class User(models.Model):
    id = models.TextField(primary_key=True)
    drop_campaigns = models.ManyToManyField(DropCampaign)
    added_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    modified_at = models.DateTimeField(blank=True, null=True, auto_now=True)

    def __str__(self) -> str:
        return self.id
