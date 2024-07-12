from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import Drop, DropCampaign, Game, Organization

# https://django-simple-history.readthedocs.io/en/latest/admin.html
admin.site.register(Drop, SimpleHistoryAdmin)
admin.site.register(DropCampaign, SimpleHistoryAdmin)
admin.site.register(Game, SimpleHistoryAdmin)
admin.site.register(Organization, SimpleHistoryAdmin)
