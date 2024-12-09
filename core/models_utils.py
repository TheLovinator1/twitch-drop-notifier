import logging
from datetime import datetime
from typing import Any

from django.db import models

logger: logging.Logger = logging.getLogger(__name__)


def wrong_typename(data: dict, expected: str) -> bool:
    """Check if the data is the expected type.

    # TODO(TheLovinator): Double check this.  # noqa: TD003
    Type name examples:
        - Game
        - DropCampaign
        - TimeBasedDrop
        - DropBenefit
        - RewardCampaign
        - Reward

    Args:
        data (dict): The data to check.
        expected (str): The expected type.

    Returns:
        bool: True if the data is not the expected type.
    """
    is_unexpected_type: bool = data.get("__typename", "") != expected
    if is_unexpected_type:
        logger.error("Not a %s? %s", expected, data)

    return is_unexpected_type


def update_field(instance: models.Model, django_field_name: str, new_value: str | datetime | None) -> int:
    """Update a field on an instance if the new value is different from the current value.

    Args:
        instance (models.Model): The Django model instance.
        django_field_name (str): The name of the field to update.
        new_value (str | datetime | None): The new value to update the field with.

    Returns:
        int: If the field was updated, returns 1. Otherwise, returns 0.
    """
    # Get the current value of the field.
    try:
        current_value = getattr(instance, django_field_name)
    except AttributeError:
        logger.exception("Field %s does not exist on %s", django_field_name, instance)
        return 0

    # Only update the field if the new value is different from the current value.
    if new_value and new_value != current_value:
        setattr(instance, django_field_name, new_value)
        return 1

    # 0 fields updated.
    return 0


def get_value(data: dict, key: str) -> datetime | str | None:
    """Get a value from a dictionary.

    We have this function so we can handle values that we need to convert to a different type. For example, we might
    need to convert a string to a datetime object.

    Args:
        data (dict): The dictionary to get the value from.
        key (str): The key to get the value for.

    Returns:
        datetime | str | None: The value from the dictionary
    """
    data_key: Any | None = data.get(key)
    if not data_key:
        return None

    # Dates are in the format "2024-08-12T05:59:59.999Z"
    dates: list[str] = ["endAt", "endsAt,", "startAt", "startsAt", "createdAt", "earnableUntil"]
    if key in dates:
        return datetime.fromisoformat(data_key.replace("Z", "+00:00"))

    return data_key


def update_fields(instance: models.Model, data: dict, field_mapping: dict[str, str]) -> int:
    """Update multiple fields on an instance using a mapping from external field names to model field names.

    Args:
        instance (models.Model): The Django model instance.
        data (dict): The new data to update the fields with.
        field_mapping (dict[str, str]): A dictionary mapping external field names to model field names.

    Returns:
        int: The number of fields updated. Used for only saving the instance if there were changes.
    """
    dirty = 0
    for json_field, django_field_name in field_mapping.items():
        data_key: datetime | str | None = get_value(data, json_field)
        dirty += update_field(instance=instance, django_field_name=django_field_name, new_value=data_key)

    if dirty > 0:
        instance.save()

    return dirty
