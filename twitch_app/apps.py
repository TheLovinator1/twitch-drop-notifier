from django.apps import AppConfig


class TwitchConfig(AppConfig):
    default_auto_field: str = "django.db.models.BigAutoField"
    name: str = "twitch_app"
