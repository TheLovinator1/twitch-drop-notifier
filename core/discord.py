import logging
from typing import TYPE_CHECKING

from discord_webhook import DiscordWebhook
from django.conf import settings
from django.utils import timezone

from core.models import DropCampaign, Game, GameSubscription, Owner, OwnerSubscription

if TYPE_CHECKING:
    from requests import Response

logger: logging.Logger = logging.getLogger(__name__)


def send(message: str, webhook_url: str | None = None) -> None:
    """Send a message to Discord.

    Args:
        message: The message to send.
        webhook_url: The webhook URL to send the message to.
    """
    logger.info("Discord message: %s", message)

    webhook_url = webhook_url or str(settings.DISCORD_WEBHOOK_URL)
    if not webhook_url:
        logger.error("No webhook URL provided.")
        return

    webhook = DiscordWebhook(
        url=webhook_url,
        content=message,
        username="TTVDrops",
        rate_limit_retry=True,
    )
    response: Response = webhook.execute()
    logger.debug(response)


def convert_time_to_discord_timestamp(time: timezone.datetime | None) -> str:
    """Discord uses <t:UNIX_TIMESTAMP:R> for timestamps.

    Args:
        time: The time to convert to a Discord timestamp.

    Returns:
        str: The Discord timestamp string. If time is None, returns "Unknown".
    """
    return f"<t:{int(time.timestamp())}:R>" if time else "Unknown"


def generate_game_message(instance: DropCampaign, game: Game, sub: GameSubscription) -> str:
    """Generate a message for a drop campaign.

    Args:
        instance (DropCampaign): Drop campaign instance.
        game (Game): Game instance.
        sub (GameSubscription): Game subscription instance.

    Returns:
        str: The message to send to Discord.
    """
    game_name: str = game.name or "Unknown"
    description: str = instance.description or "No description provided."
    start_at: str = convert_time_to_discord_timestamp(instance.starts_at)
    end_at: str = convert_time_to_discord_timestamp(instance.ends_at)
    msg: str = f"{game_name}: {instance.name}\n{description}\nStarts: {start_at}\nEnds: {end_at}"

    logger.info("Discord message: '%s' to '%s'", msg, sub.webhook.url)

    return msg


def generate_owner_message(instance: DropCampaign, owner: Owner, sub: OwnerSubscription) -> str:
    """Generate a message for a drop campaign.

    Args:
        instance (DropCampaign): Drop campaign instance.
        owner (Owner): Owner instance.
        sub (OwnerSubscription): Owner subscription instance.

    Returns:
        str: The message to send to Discord.
    """
    owner_name: str = owner.name or "Unknown"
    description: str = instance.description or "No description provided."
    start_at: str = convert_time_to_discord_timestamp(instance.starts_at)
    end_at: str = convert_time_to_discord_timestamp(instance.ends_at)
    msg: str = f"{owner_name}: {instance.name}\n{description}\nStarts: {start_at}\nEnds: {end_at}"

    logger.info("Discord message: '%s' to '%s'", msg, sub.webhook.url)

    return msg
