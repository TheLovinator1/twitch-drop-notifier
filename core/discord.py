import logging

from django.utils import timezone

logger: logging.Logger = logging.getLogger(__name__)


def convert_time_to_discord_timestamp(time: timezone.datetime | None) -> str:
    """Discord uses <t:UNIX_TIMESTAMP:R> for timestamps.

    Args:
        time: The time to convert to a Discord timestamp.

    Returns:
        str: The Discord timestamp string. If time is None, returns "Unknown".
    """
    return f"<t:{int(time.timestamp())}:R>" if time else "Unknown"
