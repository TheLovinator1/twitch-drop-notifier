from django.contrib import admin

from core.models import Benefit, DropCampaign, Game, Owner, Reward, RewardCampaign, TimeBasedDrop

admin.site.register(Game)
admin.site.register(Owner)
admin.site.register(RewardCampaign)
admin.site.register(DropCampaign)
admin.site.register(TimeBasedDrop)
admin.site.register(Benefit)
admin.site.register(Reward)
