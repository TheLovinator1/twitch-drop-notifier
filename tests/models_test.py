from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.import_json import find_typename_in_json


def test_find_typename_in_json() -> None:
    """Test the find_typename_in_json function."""
    json_file_raw: str = Path("tests/response.json").read_text(encoding="utf-8")
    json_file: dict = json.loads(json_file_raw)

    result: list[dict[str, Any]] = find_typename_in_json(json_file, typename_to_find="DropCampaign")
    assert len(result) == 20
    assert result[0]["__typename"] == "DropCampaign"
    assert result[0]["id"] == "5b5816c8-a533-11ef-9266-0a58a9feac02"
