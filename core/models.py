from django.contrib.auth.models import User
from django.db import models
from simple_history.models import HistoricalRecords

from twitch_app.models import Game


class DiscordSetting(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    webhook_url = models.URLField()
    history = HistoricalRecords()
    disabled = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"Discord: {self.user.username} - {self.name}"


class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()
    discord_webhook = models.ForeignKey(DiscordSetting, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"Subscription: {self.user.username} - {self.game.display_name} - {self.discord_webhook.name}"
