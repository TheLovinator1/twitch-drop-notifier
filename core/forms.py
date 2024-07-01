from django import forms


class DiscordSettingForm(forms.Form):
    name = forms.CharField(
        max_length=255,
        label="Name",
        required=True,
        help_text="Friendly name for knowing where the notification goes to.",
    )
    webhook_url = forms.URLField(
        label="Webhook URL",
        required=True,
        help_text="The URL to the Discord webhook. The URL can be found by right-clicking on the channel and selecting 'Edit Channel', then 'Integrations', and 'Webhooks'.",  # noqa: E501
    )
