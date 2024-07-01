from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import DiscordSetting, Subscription

# https://django-simple-history.readthedocs.io/en/latest/admin.html
admin.site.register(DiscordSetting, SimpleHistoryAdmin)
admin.site.register(Subscription, SimpleHistoryAdmin)
