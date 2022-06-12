from django.contrib import admin

from accounts.models import Component
from accounts.models import ComponentGroup
from accounts.models import Profile
from accounts.models import Team

admin.site.register(Component)
admin.site.register(ComponentGroup)
admin.site.register(Profile)
admin.site.register(Team)
