from django import template

register = template.Library()


@register.filter
def minutes_to_hours(minutes: int | None) -> str:
    """Converts minutes into 'X hours Y minutes'.

    Args:
        minutes: The number of minutes.

    Returns:
        The formatted string.
    """
    if not isinstance(minutes, int):
        return "N/A"

    hours: int = minutes // 60
    remaining_minutes: int = minutes % 60
    if hours > 0:
        if remaining_minutes > 0:
            return f"{hours}h {remaining_minutes}m"
        return f"{hours}h"
    return f"{remaining_minutes}m" if remaining_minutes > 0 else "0m"
