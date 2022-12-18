from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from accounts.models import Component
from accounts.models import ComponentGroup
from accounts.models import Profile
from accounts.models import Team
from accounts.models import TeamChatMessage


class ComponentInline(admin.TabularInline):
    model = Component


class ComponentGroupAdmin(admin.ModelAdmin):
    inlines = [
        ComponentInline,
    ]


class TeamAdminForm(forms.ModelForm):
    class Meta:
        model = Team
        exclude = []

    admins = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        label=_('Admins'),
        widget=FilteredSelectMultiple(
            verbose_name=_('Admins'),
            is_stacked=False
        )
    )
    members = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        label=_('Members'),
        widget=FilteredSelectMultiple(
            verbose_name=_('Members'),
            is_stacked=False
        )
    )


class TeamAdmin(admin.ModelAdmin):
    form = TeamAdminForm


admin.site.register(Component)
admin.site.register(ComponentGroup, ComponentGroupAdmin)
admin.site.register(Profile)
admin.site.register(Team, TeamAdmin)
admin.site.register(TeamChatMessage)
