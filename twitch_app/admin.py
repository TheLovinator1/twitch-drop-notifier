from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import DropBenefit, DropCampaign, Game, Organization, TimeBasedDrop

# https://django-simple-history.readthedocs.io/en/latest/admin.html
admin.site.register(DropBenefit, SimpleHistoryAdmin)
admin.site.register(DropCampaign, SimpleHistoryAdmin)
admin.site.register(Game, SimpleHistoryAdmin)
admin.site.register(Organization, SimpleHistoryAdmin)
admin.site.register(TimeBasedDrop, SimpleHistoryAdmin)
