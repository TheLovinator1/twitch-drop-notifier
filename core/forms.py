from django import forms
from django.core.validators import URLValidator


class DiscordSettingForm(forms.Form):
    webhook_url = forms.URLField(
        label="Webhook URL",
        required=True,
        validators=[
            URLValidator(
                schemes=["https"],
                message="The URL must be a valid HTTPS URL.",
            ),
            URLValidator(
                regex=r"https://discord.com/api/webhooks/\d{18}/[a-zA-Z0-9_-]{68}",
                message="The URL must be a valid Discord webhook URL.",
            ),
        ],
        help_text="The URL can be found by right-clicking on the channel and selecting 'Edit Channel', then 'Integrations', and 'Webhooks'.",  # noqa: E501
    )
