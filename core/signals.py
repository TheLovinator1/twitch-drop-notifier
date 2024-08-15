import logging
from typing import TYPE_CHECKING

from discord_webhook import DiscordWebhook
from django.db.models.manager import BaseManager
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from core.models import DropCampaign, Game, GameSubscription, Owner, OwnerSubscription

if TYPE_CHECKING:
    import requests
    from django.db.models.manager import BaseManager

logger: logging.Logger = logging.getLogger(__name__)


def convert_time_to_discord_timestamp(time: timezone.datetime | None) -> str:
    """Discord uses <t:UNIX_TIMESTAMP:R> for timestamps.

    Args:
        time: The time to convert to a Discord timestamp.

    Returns:
        str: The Discord timestamp string. If time is None, returns "Unknown".
    """
    return f"<t:{int(time.timestamp())}:R>" if time else "Unknown"


@receiver(signal=post_save, sender=DropCampaign)
def notify_users_of_new_drop(sender: DropCampaign, instance: DropCampaign, created: bool, **kwargs) -> None:  # noqa: ANN003, ARG001, FBT001
    """Notify users of a new drop campaign.

    Args:
        sender (DropCampaign): The model we are sending the signal from.
        instance (DropCampaign): The instance of the model that was created.
        created (bool): Whether the instance was created or updated.
        **kwargs: Additional keyword arguments.
    """
    if not created:
        logger.debug("Drop campaign '%s' was updated.", instance.name)
        return

    game: Game | None = instance.game
    if not game:
        return

    owner: Owner = game.owner  # type: ignore  # noqa: PGH003

    # Notify users subscribed to the game
    game_subs: BaseManager[GameSubscription] = GameSubscription.objects.filter(game=game)
    for sub in game_subs:
        if not sub.webhook.url:
            logger.error("No webhook URL provided.")
            return

        webhook = DiscordWebhook(
            url=sub.webhook.url,
            content=generate_game_message(instance=instance, game=game, sub=sub),
            username=f"{game.name} drop.",
            rate_limit_retry=True,
        )
        response: requests.Response = webhook.execute()
        logger.debug(response)

    # Notify users subscribed to the owner
    owner_subs: BaseManager[OwnerSubscription] = OwnerSubscription.objects.filter(owner=owner)
    for sub in owner_subs:
        if not sub.webhook.url:
            logger.error("No webhook URL provided.")
            return

        webhook = DiscordWebhook(
            url=sub.webhook.url,
            content=generate_owner_message(instance=instance, owner=owner, sub=sub),
            username=f"{owner.name} drop.",
            rate_limit_retry=True,
        )
        response: requests.Response = webhook.execute()
        logger.debug(response)


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
