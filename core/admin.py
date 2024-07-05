from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import Webhook

# https://django-simple-history.readthedocs.io/en/latest/admin.html
admin.site.register(Webhook, SimpleHistoryAdmin)
