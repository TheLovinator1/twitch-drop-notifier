from django import template

register = template.Library()


@register.filter(name="trim")
def trim(value: str) -> str:
    """Trim the value.

    Args:
        value: The value to trim.

    Returns:
        The trimmed value.
    """
    return value.strip()
