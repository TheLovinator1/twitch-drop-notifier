from django.contrib import admin

from .models import DiscordSetting, Subscription

admin.site.register(DiscordSetting)
admin.site.register(Subscription)
