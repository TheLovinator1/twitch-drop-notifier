import logging
import os
from typing import TYPE_CHECKING

from discord_webhook import DiscordWebhook
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.discord import convert_time_to_discord_timestamp
from core.models import DropCampaign, Game, Owner, User, Webhook

if TYPE_CHECKING:
    import requests

logger: logging.Logger = logging.getLogger(__name__)


def generate_message(game: Game, drop: DropCampaign) -> str:
    """Generate a message for a game.

    Args:
        game (Game): The game to generate a message for.
        drop (DropCampaign): The drop campaign to generate a message for.

    Returns:
        str: The message.
    """
    # TODO(TheLovinator): Add a twitch link to a stream that has drops enabled.  # noqa: TD003
    game_name: str = game.name or "Unknown game"
    description: str = drop.description or "No description available."
    start_at: str = convert_time_to_discord_timestamp(drop.starts_at)
    end_at: str = convert_time_to_discord_timestamp(drop.ends_at)
    msg: str = f"**{game_name}**\n\n{description}\n\nStarts: {start_at}\nEnds: {end_at}"

    logger.debug(msg)

    return msg


@receiver(signal=post_save, sender=User)
def handle_user_signed_up(sender: User, instance: User, created: bool, **kwargs) -> None:  # noqa: ANN003, ARG001, FBT001
    """Send a message to Discord when a user signs up.

    Webhook URL is read from .env file.

    Args:
        sender (User): The model we are sending the signal from.
        instance (User): The instance of the model that was created.
        created (bool): Whether the instance was created or updated.
        **kwargs: Additional keyword arguments.
    """
    if not created:
        logger.debug("User '%s' was updated.", instance.username)
        return

    webhook_url: str | None = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        logger.error("No webhook URL provided.")
        return

    webhook = DiscordWebhook(
        url=webhook_url,
        content=f"New user signed up: '{instance.username}'",
        username="TTVDrops",
        rate_limit_retry=True,
    )
    response: requests.Response = webhook.execute()
    logger.debug(response)


def notify_users_of_new_drop(sender: DropCampaign, instance: DropCampaign, created: bool, **kwargs) -> None:  # noqa: ANN003, ARG001, FBT001
    """Send message to all webhooks subscribed to new drops.

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
        logger.error("No game found. %s", instance)
        return

    if game.owner:  # type: ignore  # noqa: PGH003
        handle_owner_drops(instance, game)
    else:
        logger.error("No owner found. %s", instance)

    if game := instance.game:
        handle_game_drops(instance, game)
    else:
        logger.error("No game found. %s", instance)


def handle_game_drops(instance: DropCampaign, game: Game) -> None:
    """Send message to all webhooks subscribed to new drops for this game.

    Args:
        instance (DropCampaign): The drop campaign that was created.
        game (Game): The game that the drop campaign is for.
    """
    webhooks: list[Webhook] = game.subscribed_new_games.all()  # type: ignore  # noqa: PGH003
    for hook in webhooks:
        # Don't spam the same drop campaign.
        if hook in hook.seen_drops.all():
            logger.error("Already seen drop campaign '%s'.", instance.name)
            continue

            # Set the webhook as seen so we don't spam it.
        hook.seen_drops.add(instance)

        # Send the webhook.
        webhook_url: str = hook.get_webhook_url()
        if not webhook_url:
            logger.error("No webhook URL provided.")
            continue

        webhook = DiscordWebhook(
            url=webhook_url,
            content=generate_message(game, instance),
            username=f"{game.name} Twitch drops",
            rate_limit_retry=True,
        )
        response: requests.Response = webhook.execute()
        logger.debug(response)


def handle_owner_drops(instance: DropCampaign, game: Game) -> None:
    """Send message to all webhooks subscribed to new drops for this owner/organization.

    Args:
        instance (DropCampaign): The drop campaign that was created.
        game (Game): The game that the drop campaign is for.
    """
    owner: Owner = game.owner  # type: ignore  # noqa: PGH003
    webhooks: list[Webhook] = owner.subscribed_new_games.all()  # type: ignore  # noqa: PGH003
    for hook in webhooks:
        # Don't spam the same drop campaign.
        if hook in hook.seen_drops.all():
            logger.error("Already seen drop campaign '%s'.", instance.name)
            continue

            # Set the webhook as seen so we don't spam it.
        hook.seen_drops.add(instance)

        # Send the webhook.
        webhook_url: str = hook.get_webhook_url()
        if not webhook_url:
            logger.error("No webhook URL provided.")
            continue

        webhook = DiscordWebhook(
            url=webhook_url,
            content=generate_message(game, instance),
            username=f"{game.name} Twitch drops",
            rate_limit_retry=True,
        )
        response: requests.Response = webhook.execute()
        logger.debug(response)
