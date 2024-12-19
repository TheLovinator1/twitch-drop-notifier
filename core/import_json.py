from __future__ import annotations

import logging
from typing import Any, Literal

from core.models import Benefit, DropCampaign, Game, Owner, TimeBasedDrop

logger: logging.Logger = logging.getLogger(__name__)


type_names = Literal["Organization", "Game", "DropCampaign", "TimeBasedDrop", "DropBenefit", "RewardCampaign", "Reward"]


def import_data(data: dict[str, Any]) -> None:
    """Import the data from the JSON object.

    This looks for '__typename' with the value 'DropCampaign' in the JSON object and imports the data.

    Args:
        data (dict[str, Any]): The data to import.
    """
    drop_campaigns: list[dict[str, Any]] = find_typename_in_json(json_obj=data, typename_to_find="DropCampaign")
    for drop_campaign_json in drop_campaigns:
        import_drop_campaigns(drop_campaigns=drop_campaign_json)


def import_drop_campaigns(drop_campaigns: dict[str, Any]) -> DropCampaign | None:
    """Import the drop campaigns from the data.

    Args:
        drop_campaigns (dict[str, Any]): The drop campaign data.

    Returns:
        DropCampaign | None: The drop campaign instance if created, otherwise None
    """
    twitch_id: str = drop_campaigns.get("id", "")
    logger.info("\tProcessing drop campaign: %s", twitch_id)

    if not twitch_id:
        logger.error("\tDrop campaign has no ID: %s", drop_campaigns)
        return None

    drop_campaign, created = DropCampaign.objects.get_or_create(twitch_id=twitch_id)
    if created:
        logger.info("\tCreated drop campaign: %s", drop_campaign)

    owner: Owner = import_owner_data(drop_campaign=drop_campaigns)
    game: Game = import_game_data(drop_campaign=drop_campaigns, owner=owner)
    drop_campaign.import_json(data=drop_campaigns, game=game)

    import_time_based_drops(drop_campaigns, drop_campaign)

    return drop_campaign


def import_time_based_drops(drop_campaign_json: dict[str, Any], drop_campaign: DropCampaign) -> list[TimeBasedDrop]:
    """Import the time-based drops from a drop campaign.

    Args:
        drop_campaign_json (dict[str, Any]): The drop campaign data.
        drop_campaign (DropCampaign): The drop campaign instance.

    Returns:
        list[TimeBasedDrop]: The imported time-based drops.
    """
    imported_drops: list[TimeBasedDrop] = []
    time_based_drops: list[dict[str, Any]] = find_typename_in_json(drop_campaign_json, "TimeBasedDrop")
    for time_based_drop_json in time_based_drops:
        time_based_drop_id: str = time_based_drop_json.get("id", "")
        if not time_based_drop_id:
            logger.error("\tTime-based drop has no ID: %s", time_based_drop_json)
            continue

        time_based_drop, created = TimeBasedDrop.objects.get_or_create(twitch_id=time_based_drop_id)
        if created:
            logger.info("\tCreated time-based drop: %s", time_based_drop)

        time_based_drop.import_json(time_based_drop_json, drop_campaign)

        import_drop_benefits(time_based_drop_json, time_based_drop)
        imported_drops.append(time_based_drop)

    return imported_drops


def import_drop_benefits(time_based_drop_json: dict[str, Any], time_based_drop: TimeBasedDrop) -> list[Benefit]:
    """Import the drop benefits from a time-based drop.

    Args:
        time_based_drop_json (dict[str, Any]): The time-based drop data.
        time_based_drop (TimeBasedDrop): The time-based drop instance.

    Returns:
        list[Benefit]: The imported drop benefits.
    """
    drop_benefits: list[Benefit] = []
    benefits: list[dict[str, Any]] = find_typename_in_json(time_based_drop_json, "DropBenefit")
    for benefit_json in benefits:
        benefit_id: str = benefit_json.get("id", "")
        if not benefit_id:
            logger.error("\tBenefit has no ID: %s", benefit_json)
            continue

        benefit, created = Benefit.objects.get_or_create(twitch_id=benefit_id)
        if created:
            logger.info("\tCreated benefit: %s", benefit)

        benefit.import_json(benefit_json, time_based_drop)
        drop_benefits.append(benefit)

    return drop_benefits


def import_owner_data(drop_campaign: dict[str, Any]) -> Owner:
    """Import the owner data from a drop campaign.

    Args:
        drop_campaign (dict[str, Any]): The drop campaign data.

    Returns:
        Owner: The owner instance.
    """
    owner_data_list: list[dict[str, Any]] = find_typename_in_json(drop_campaign, "Organization")
    for owner_data in owner_data_list:
        owner_id: str = owner_data.get("id", "")
        if not owner_id:
            logger.error("\tOwner has no ID: %s", owner_data)
            continue

        owner, created = Owner.objects.get_or_create(twitch_id=owner_id)
        if created:
            logger.info("\tCreated owner: %s", owner)

        owner.import_json(owner_data)
    return owner


def import_game_data(drop_campaign: dict[str, Any], owner: Owner) -> Game:
    """Import the game data from a drop campaign.

    Args:
        drop_campaign (dict[str, Any]): The drop campaign data.
        owner (Owner): The owner of the game.

    Returns:
        Game: The game instance.
    """
    game_data_list: list[dict[str, Any]] = find_typename_in_json(drop_campaign, "Game")
    for game_data in game_data_list:
        game_id: str = game_data.get("id", "")
        if not game_id:
            logger.error("\tGame has no ID: %s", game_data)
            continue

        game, created = Game.objects.get_or_create(twitch_id=game_id)
        if created:
            logger.info("\tCreated game: %s", game)

        game.import_json(game_data, owner)
    return game


def find_typename_in_json(json_obj: list | dict, typename_to_find: type_names) -> list[dict[str, Any]]:
    """Recursively search for '__typename' in a JSON object and return dictionaries where '__typename' equals the specified value.

    Args:
        json_obj (list | dict): The JSON object to search.
        typename_to_find (str): The '__typename' value to search for.

    Returns:
        A list of dictionaries where '__typename' equals the specified value.
    """  # noqa: E501
    matching_dicts: list[dict[str, Any]] = []

    if isinstance(json_obj, dict):
        # Check if '__typename' exists and matches the value
        if json_obj.get("__typename") == typename_to_find:
            matching_dicts.append(json_obj)
        # Recurse into the dictionary
        for value in json_obj.values():
            matching_dicts.extend(find_typename_in_json(value, typename_to_find))
    elif isinstance(json_obj, list):
        # Recurse into each item in the list
        for item in json_obj:
            matching_dicts.extend(find_typename_in_json(item, typename_to_find))

    return matching_dicts
