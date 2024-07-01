from django.contrib import admin

from .models import DropBenefit, DropCampaign, Game, Organization, TimeBasedDrop

admin.site.register(DropBenefit)
admin.site.register(DropCampaign)
admin.site.register(Game)
admin.site.register(Organization)
admin.site.register(TimeBasedDrop)
