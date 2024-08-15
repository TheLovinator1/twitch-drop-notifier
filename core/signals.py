import logging
import os
from typing import TYPE_CHECKING

from discord_webhook import DiscordWebhook
from django.db.models.manager import BaseManager
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.discord import generate_game_message, generate_owner_message
from core.models import DropCampaign, Game, GameSubscription, Owner, OwnerSubscription, User

if TYPE_CHECKING:
    import requests
    from django.db.models.manager import BaseManager

logger: logging.Logger = logging.getLogger(__name__)


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
