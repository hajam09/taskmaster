from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from jira.models import Board
from jira.models import Column
from jira.models import ColumnStatus
from jira.models import Label
from jira.models import Project
from jira.models import ProjectComponent
from jira.models import Sprint
from jira.models import Ticket
from jira.models import TicketAttachment
from jira.models import TicketComment


class BoardAdminForm(forms.ModelForm):
    class Meta:
        model = Board
        exclude = []

    projects = forms.ModelMultipleChoiceField(
        queryset=Project.objects.all(),
        required=False,
        label=_('Projects'),
        widget=FilteredSelectMultiple(
            verbose_name=_('Projects'),
            is_stacked=False
        )
    )
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


class BoardAdmin(admin.ModelAdmin):
    form = BoardAdminForm


class ProjectAdminForm(forms.ModelForm):
    class Meta:
        model = Project
        exclude = []

    members = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        label=_('Members'),
        widget=FilteredSelectMultiple(
            verbose_name=_('Members'),
            is_stacked=False
        )
    )
    watchers = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        label=_('Watchers'),
        widget=FilteredSelectMultiple(
            verbose_name=_('Watchers'),
            is_stacked=False
        )
    )


class ProjectAdmin(admin.ModelAdmin):
    form = ProjectAdminForm


class SprintAdminForm(forms.ModelForm):
    class Meta:
        model = Sprint
        exclude = []

    tickets = forms.ModelMultipleChoiceField(
        queryset=Ticket.objects.all(),
        required=False,
        label=_('Tickets'),
        widget=FilteredSelectMultiple(
            verbose_name=_('Tickets'),
            is_stacked=False
        )
    )


class SprintAdmin(admin.ModelAdmin):
    form = SprintAdminForm


class TicketAdminForm(forms.ModelForm):
    class Meta:
        model = Ticket
        exclude = []

    subTask = forms.ModelMultipleChoiceField(
        queryset=Ticket.objects.all(),
        required=False,
        label=_('SubTask'),
        widget=FilteredSelectMultiple(
            verbose_name=_('SubTask'),
            is_stacked=False
        )
    )
    component = forms.ModelMultipleChoiceField(
        queryset=ProjectComponent.objects.all(),
        required=False,
        label=_('Component'),
        widget=FilteredSelectMultiple(
            verbose_name=_('Component'),
            is_stacked=False
        )
    )
    linkedIssues = forms.ModelMultipleChoiceField(
        queryset=Ticket.objects.all(),
        required=False,
        label=_('LinkedIssues'),
        widget=FilteredSelectMultiple(
            verbose_name=_('LinkedIssues'),
            is_stacked=False
        )
    )
    label = forms.ModelMultipleChoiceField(
        queryset=Label.objects.all(),
        required=False,
        label=_('Label'),
        widget=FilteredSelectMultiple(
            verbose_name=_('Label'),
            is_stacked=False
        )
    )
    watchers = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        label=_('Watchers'),
        widget=FilteredSelectMultiple(
            verbose_name=_('Watchers'),
            is_stacked=False
        )
    )


class TicketAdmin(admin.ModelAdmin):
    form = TicketAdminForm


admin.site.register(Board, BoardAdmin)
admin.site.register(Column)
admin.site.register(ColumnStatus)
admin.site.register(Label)
admin.site.register(Project, ProjectAdmin)
admin.site.register(ProjectComponent)
admin.site.register(Sprint, SprintAdmin)
admin.site.register(Ticket, TicketAdmin)
admin.site.register(TicketAttachment)
admin.site.register(TicketComment)
