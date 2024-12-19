from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from core.import_json import (
    find_typename_in_json,
    import_drop_benefits,
    import_drop_campaigns,
    import_game_data,
    import_owner_data,
    import_time_based_drops,
    type_names,
)
from core.models import Benefit, DropCampaign, Game, Owner, TimeBasedDrop


def _validate_extraction(json: dict, typename: type_names, no_result_err_msg: str, id_err_msg: str) -> dict[str, Any]:
    result: dict[str, Any] = find_typename_in_json(json, typename)[0]
    assert result, no_result_err_msg
    assert result.get("id"), id_err_msg

    return result


def test_find_typename_in_json() -> None:
    """Test the find_typename_in_json function."""
    json_file_raw: str = Path("tests/response.json").read_text(encoding="utf-8")
    json_file: dict = json.loads(json_file_raw)

    result: list[dict[str, Any]] = find_typename_in_json(json_file, typename_to_find="DropCampaign")
    assert len(result) == 20
    assert result[0]["__typename"] == "DropCampaign"
    assert result[0]["id"] == "5b5816c8-a533-11ef-9266-0a58a9feac02"


@pytest.mark.django_db
def test_import_game_data() -> None:
    """Test the import_game_data function."""
    json_file_raw: str = Path("tests/response.json").read_text(encoding="utf-8")
    json_file: dict = json.loads(json_file_raw)

    game_json: dict[str, Any] = _validate_extraction(
        json=json_file,
        typename="Game",
        no_result_err_msg="Game JSON not found",
        id_err_msg="Game ID not found",
    )
    assert game_json.get("id") == "155409827", f"Game ID does not match expected value: {game_json.get('id')}"
    assert game_json.get("slug") == "pokemon-trading-card-game-live", "Game slug does not match expected value"

    assert_msg: str = f"Game display name does not match expected value: {game_json.get('displayName')}"
    assert game_json.get("displayName") == "Pokémon Trading Card Game Live", assert_msg

    assert_msg: str = f"Game URL does not match expected value: {game_json.get('gameUrl')}"
    assert game_json.get("__typename") == "Game", assert_msg

    owner_json: dict[str, Any] = _validate_extraction(
        json=json_file,
        typename="Organization",
        no_result_err_msg="Owner JSON not found",
        id_err_msg="Owner ID not found",
    )

    owner, created = Owner.objects.get_or_create(twitch_id=owner_json.get("id"))
    assert_msg: str = f"Owner was not created: {owner=} != {owner_json.get('id')}. This means the old database was used instead of a new one."  # noqa: E501
    assert created, assert_msg
    assert owner

    game: Game = import_game_data(drop_campaign=game_json, owner=owner)
    assert game, f"Failed to import JSON data into Game model: {game_json=}"
    assert game.org == owner, f"Owner was not set on the Game model: {game.org=} != {owner=}"
    assert game.display_name == game_json.get("displayName"), "Game display name was not set on the Game model"

    assert_msg: str = f"Game slug was not set on the Game model: {game.slug=} != {game_json.get('slug')}"
    assert game.slug == game_json.get("slug"), assert_msg

    assert_msg: str = f"Game ID was not set on the Game model: {game.twitch_id=} != {game_json.get('id')}"
    assert game.twitch_id == game_json.get("id"), assert_msg

    assert_msg: str = f"Game URL was not set on the Game model: {game.game_url} != https://www.twitch.tv/directory/category/{game.slug}"
    assert game.game_url == f"https://www.twitch.tv/directory/category/{game.slug}", assert_msg

    assert game.created_at, "Game created_at was not set on the Game model"
    assert game.modified_at, "Game modified_at was not set on the Game model"


@pytest.mark.django_db
def test_import_owner_data() -> None:
    """Test the import_owner_data function."""
    json_file_raw: str = Path("tests/response.json").read_text(encoding="utf-8")
    json_file: dict = json.loads(json_file_raw)

    owner_json: dict[str, Any] = _validate_extraction(
        json=json_file,
        typename="Organization",
        no_result_err_msg="Owner JSON not found",
        id_err_msg="Owner ID not found",
    )

    owner: Owner = import_owner_data(drop_campaign=owner_json)
    assert owner, f"Failed to import JSON data into Owner model: {owner_json=}"

    assert_msg: str = f"Owner ID was not set on the Owner model: {owner.twitch_id=} != {owner_json.get('id')}"
    assert owner.twitch_id == owner_json.get("id"), assert_msg

    assert_msg: str = f"Owner name was not set on the Owner model: {owner.name=} != {owner_json.get('name')}"
    assert owner.name == owner_json.get("name"), assert_msg

    assert owner.created_at, "Owner created_at was not set on the Owner model"
    assert owner.modified_at, "Owner modified_at was not set on the Owner model"


@pytest.mark.django_db
def test_import_drop_benefits() -> None:
    """Test the import_drop_benefits function."""
    json_file_raw: str = Path("tests/response.json").read_text(encoding="utf-8")
    json_file: dict = json.loads(json_file_raw)

    drop_campaign_json: dict[str, Any] = _validate_extraction(
        json=json_file,
        typename="DropCampaign",
        no_result_err_msg="DropCampaign JSON not found",
        id_err_msg="DropCampaign ID not found",
    )
    assert drop_campaign_json

    drop_campaign: DropCampaign | None = import_drop_campaigns(drop_campaigns=drop_campaign_json)
    assert drop_campaign, f"Failed to import JSON data into DropCampaign model: {drop_campaign_json=}"

    assert find_typename_in_json(drop_campaign_json, "TimeBasedDrop"), "TimeBasedDrop JSON not found"
    time_based_drop_json: dict[str, Any] = _validate_extraction(
        json=drop_campaign_json,
        typename="TimeBasedDrop",
        no_result_err_msg="TimeBasedDrop JSON not found",
        id_err_msg="TimeBasedDrop ID not found",
    )
    assert time_based_drop_json

    time_based_drop: list[TimeBasedDrop] = import_time_based_drops(
        drop_campaign_json=time_based_drop_json,
        drop_campaign=drop_campaign,
    )
    assert time_based_drop, f"Failed to import JSON data into TimeBasedDrop model: {time_based_drop_json=}"

    drop_benefit_json: dict[str, Any] = _validate_extraction(
        json=drop_campaign_json,
        typename="DropBenefit",
        no_result_err_msg="DropBenefit JSON not found",
        id_err_msg="DropBenefit ID not found",
    )

    drop_benefit: list[Benefit] = import_drop_benefits(drop_benefit_json, time_based_drop[0])
    assert drop_benefit, f"Failed to import JSON data into DropBenefit model: {drop_benefit_json=}"
    assert drop_benefit[0].twitch_id == drop_benefit_json.get("id"), "Benefit ID was not set on the Benefit model"

    assert_msg: str = f"DropBenefit created_at was not set on the Benefit model: {drop_benefit[0].created_at=}"
    assert drop_benefit[0].created_at, assert_msg

    assert_msg = f"DropBenefit modified_at was not set on the Benefit model: {drop_benefit[0].modified_at=}"
    assert drop_benefit[0].modified_at, assert_msg

    assert drop_benefit[0].time_based_drop == time_based_drop[0], "TimeBasedDrop was not set on the Benefit model"
