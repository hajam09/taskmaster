from django.contrib import admin

from accounts.models import Component
from accounts.models import ComponentGroup
from accounts.models import Profile
from accounts.models import Team


class ComponentInline(admin.TabularInline):
    model = Component


class ComponentGroupAdmin(admin.ModelAdmin):
    inlines = [
        ComponentInline,
    ]


admin.site.register(Component)
admin.site.register(ComponentGroup, ComponentGroupAdmin)
admin.site.register(Profile)
admin.site.register(Team)
