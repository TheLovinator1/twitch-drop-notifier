from typing import Literal

import auto_prefetch
from django.db import models
from simple_history.models import HistoricalRecords

from twitch_app.models import Game


class Webhook(auto_prefetch.Model):
    """Webhooks to send notifications to."""

    url = models.URLField(unique=True)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    disabled = models.BooleanField(default=False)
    added_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    modified_at = models.DateTimeField(blank=True, null=True, auto_now=True)
    history = HistoricalRecords()

    class Meta(auto_prefetch.Model.Meta):
        verbose_name: str = "Webhook"
        verbose_name_plural: str = "Webhooks"
        ordering: tuple[Literal["url"]] = ("url",)

    def __str__(self) -> str:
        return self.url
