from django.contrib import admin

from core.models import Benefit, DropCampaign, Game, Owner, TimeBasedDrop

admin.site.register(Game)
admin.site.register(Owner)
admin.site.register(DropCampaign)
admin.site.register(TimeBasedDrop)
admin.site.register(Benefit)
