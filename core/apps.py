from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field: str = "django.db.models.BigAutoField"
    name = "core"

    @staticmethod
    def ready() -> None:
        """Ready runs on app startup.

        We import signals here so that they are registered when the app starts.
        """
        import core.signals  # noqa: F401, PLC0415
