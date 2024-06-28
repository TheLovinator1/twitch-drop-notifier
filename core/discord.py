import logging
from typing import TYPE_CHECKING

from discord_webhook import DiscordWebhook
from django.conf import settings

if TYPE_CHECKING:
    from requests import Response

logger: logging.Logger = logging.getLogger(__name__)


def send(message: str) -> None:
    """Send a message to Discord.

    Args:
        message: The message to send.
    """
    webhook_url = str(settings.DISCORD_WEBHOOK_URL)
    if not webhook_url:
        logger.error("No Discord webhook URL found.")
        return

    webhook = DiscordWebhook(
        url=webhook_url,
        content=message,
        username="TTVDrops",
        rate_limit_retry=True,
    )
    response: Response = webhook.execute()
    logger.debug(response)
