from django.contrib import admin

from hicap.membership.models import Maker

class MakerAdmin(admin.ModelAdmin):
	pass


admin.site.register(Maker, MakerAdmin)
