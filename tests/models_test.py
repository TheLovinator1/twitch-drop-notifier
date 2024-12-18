from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from core.import_json import find_typename_in_json, import_game_data, type_names
from core.models import Game, Owner


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
    owner_json: dict[str, Any] = _validate_extraction(
        json=json_file,
        typename="Organization",
        no_result_err_msg="Owner JSON not found",
        id_err_msg="Owner ID not found",
    )
    owner, created = Owner.objects.get_or_create(twitch_id=owner_json.get("id"))
    assert created, "Owner was not created so the old database was not cleared for some reason"

    game: Game = import_game_data(drop_campaign=game_json, owner=owner)
    assert game, "Failed to import JSON data into Game model"
