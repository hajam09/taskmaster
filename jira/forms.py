from datetime import datetime

from django import forms
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.exceptions import ValidationError

from accounts.models import Profile, ComponentGroup, Component, Team
from jira.models import Project, Board


class TeamForm(forms.Form):
    name = forms.CharField(
        label='Name',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control col',
                'placeholder': 'Team name',

            }
        ),
    )
    description = forms.CharField(
        label='Description',
        widget=forms.Textarea(
            attrs={
                'class': 'form-control col',
                'placeholder': 'Team description',
                'rows': 5,
            }
        )
    )
    admins = forms.MultipleChoiceField(
        label='Admins',
        widget=forms.Select(
            attrs={
                'class': 'form-control select2bs4 teamAdmins',
                'multiple': 'multiple',
                'style': 'width: 100%',
                'required': 'required',
            }
        ),
    )
    members = forms.MultipleChoiceField(
        label='Members',
        widget=forms.Select(
            attrs={
                'class': 'form-control select2bs4 teamMembers',
                'multiple': 'multiple',
                'style': 'width: 100%',
                'required': 'required',
            }
        ),
    )
    visibility = forms.ChoiceField(
        label='Visibility',
        choices=[('EVERYONE', 'Everyone'), ('MEMBERS', 'Members')],
        widget=forms.RadioSelect(
        )
    )

    def __init__(self, request, *args, **kwargs):
        super(TeamForm, self).__init__(*args, **kwargs)
        self.request = request
        userChoices = [(str(i.user.id), i.user.get_full_name()) for i in Profile.objects.all().select_related('user')]
        self.base_fields['admins'].choices = userChoices
        self.base_fields['members'].choices = userChoices
        self.base_fields['visibility'].initial = 'EVERYONE'

    def clean(self):
        super(TeamForm, self).clean()
        name = self.cleaned_data.get("name")
        if Team.objects.filter(internalKey=name).exists():
            messages.error(
                self.request,
                f'Team with name {name} already exists.'
            )
            raise ValidationError({'name': [f'Team with name {name} already exists!', ]})
        return self.cleaned_data

    def save(self):
        team = Team()
        team.internalKey = self.cleaned_data.get("name")
        team.description = self.cleaned_data.get("description")
        team.isPrivate = self.cleaned_data.get("visibility") == 'MEMBERS'
        team.save()

        team.admins.add(*self.request.POST.getlist('admins'))
        team.members.add(*self.request.POST.getlist('members'))
        return team


class TicketCreationForm(forms.Form):
    project = forms.ChoiceField(
        label='Project',
        widget=forms.Select(
            attrs={
                'class': 'form-control'
            }
        ),
    )
    issueType = forms.ChoiceField(
        label='Issue type',
        widget=forms.Select(
            attrs={
                'class': 'form-control'
            }
        ),
    )
    #
    summary = forms.CharField(
        label='Summary',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Summary',

            }
        ),
    )
    priority = forms.ChoiceField(
        label='Priority',
        widget=forms.Select(
            attrs={
                'class': 'form-control'
            }
        ),
    )
    storyPoints = forms.IntegerField(
        label='Story points',
        widget=forms.NumberInput(
            attrs={
                'class': 'form-control'
            }
        ),
    )
    description = forms.CharField(
        label='Description',
        widget=forms.Textarea(
            attrs={
                'class': 'form-control',
                'rows': 5,
            }
        )

    )
    board = forms.ChoiceField(
        label='Board',
        widget=forms.Select(
            attrs={
                'class': 'form-control'
            }
        ),
    )
    assignee = forms.ChoiceField(
        label='Assignee',
        widget=forms.Select(
            attrs={
                'class': 'form-control'
            }
        ),
    )

    def __init__(self, request, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super(TicketCreationForm, self).__init__(*args, **kwargs)

        projectChoices = [(str(i.id), i.internalKey) for i in Project.objects.all()]
        self.base_fields['project'].choices = projectChoices

        issueTypeChoices = [(str(i.id), i.internalKey) for i in cache.get('TICKET_ISSUE_TYPE')]
        self.base_fields['issueType'].choices = issueTypeChoices

        priorityChoices = [(str(i.id), i.internalKey) for i in cache.get('TICKET_PRIORITY')]
        self.base_fields['priority'].choices = priorityChoices

        boardChoices = [(str(i.id), i.internalKey) for i in Board.objects.all()]
        self.base_fields['board'].choices = boardChoices

        assigneeChoices = [(str(i.id), i.get_full_name()) for i in User.objects.all()]
        self.base_fields['assignee'].choices = assigneeChoices

        if request.user.is_authenticated:
            self.base_fields['assignee'].initial = request.user.id


class ProjectSettingsForm(forms.Form):
    name = forms.CharField(
        label='Name',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control col',
                'placeholder': 'Project name',

            }
        ),
    )
    key = forms.CharField(
        label='Key',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control col',
                'placeholder': 'Project code',

            }
        ),
    )
    lead = forms.ChoiceField(
        label='Lead',
        widget=forms.Select(
            attrs={
                'class': 'form-control select2bs4'
            }
        ),
    )
    status = forms.ChoiceField(
        label='Status',
        widget=forms.Select(
            attrs={
                'class': 'form-control select2bs4'
            }
        ),
    )
    startDate = forms.DateField(
        label='Start Date',
        widget=forms.DateInput(
            attrs={
                'class': 'form-control col flatpickr',
                'type': 'date'
            }
        )
    )
    endDate = forms.DateField(
        label='End Date',
        widget=forms.DateInput(
            attrs={
                'class': 'form-control col flatpickr',
                'type': 'date'
            }
        )
    )
    description = forms.CharField(
        label='Description',
        widget=forms.Textarea(
            attrs={
                'class': 'form-control col',
                'placeholder': 'Project description',
                'rows': 3,
            }
        )

    )
    members = forms.MultipleChoiceField(
        label='Project members',
        widget=forms.Select(
            attrs={
                'class': 'form-control select2bs4 project-members',
                'multiple': 'multiple'
            }
        ),
    )

    components = forms.MultipleChoiceField(
        label='Project components',
        widget=forms.Select(
            attrs={
                'class': 'form-control select2bs4Tags project-components',
                'multiple': 'multiple'
            }
        ),
    )
    visibility = forms.ChoiceField(
        label='Project visibility',
        choices=[('EVERYONE', 'Everyone'), ('MEMBERS', 'Members')],
        widget=forms.RadioSelect(
        )
    )

    def __init__(self, request, project, *args, **kwargs):
        super(ProjectSettingsForm, self).__init__(*args, **kwargs)
        self.request = request
        self.project = project

        self.base_fields['name'].initial = self.project.internalKey

        self.base_fields['key'].initial = self.project.code
        self.base_fields['key'].disabled = True

        leadChoices = [(str(i.user.id), i.user.get_full_name()) for i in Profile.objects.all().select_related('user')]
        self.base_fields['lead'].choices = leadChoices
        self.base_fields['lead'].initial = str(self.project.lead.id)

        statusChoices = [(str(i.id), i.internalKey) for i in cache.get('PROJECT_STATUS')]
        self.base_fields['status'].choices = statusChoices
        self.base_fields['status'].initial = str(self.project.status_id)

        self.base_fields['startDate'].initial = self.project.startDate
        self.base_fields['endDate'].initial = self.project.endDate

        self.base_fields['description'].initial = self.project.description

        self.base_fields['members'].choices = leadChoices

        componentsChoices = [
            (str(i.internalKey), i.internalKey)
            for i in Component.objects.filter(componentGroup__code='PROJECT_COMPONENTS')
            if i.reference == self.project.code
        ]
        """
        # WIP
        componentsChoices = [
            (i[0], i[0])
            for i in Component.objects.filter(componentGroup__code='PROJECT_COMPONENTS').values_list('internalKey', 'reference')
            if i[1] == self.project.code
        ]        
        """

        self.base_fields['components'].choices = componentsChoices
        self.base_fields['visibility'].initial = 'MEMBERS' if self.project.isPrivate else 'EVERYONE'

    def save(self):
        self.project.internalKey = self.data.get('name')
        self.project.description = self.data.get('description')
        self.project.lead_id = self.data.get('lead')
        self.project.status_id = self.data.get('status')
        self.project.startDate = datetime.strptime(self.data.get('startDate'), "%Y-%m-%d").date()
        self.project.endDate = datetime.strptime(self.data.get('endDate'), "%Y-%m-%d").date()
        self.project.isPrivate = self.data.get('visibility') == 'MEMBERS'

        self.project.members.clear()
        self.project.members.add(*self.request.POST.getlist('members'))

        componentGroup = ComponentGroup.objects.get(code='PROJECT_COMPONENTS')
        updatedComponents = self.data.getlist('components')

        componentsList = list(Component.objects.filter(
            componentGroup__code='PROJECT_COMPONENTS',
            internalKey__in=updatedComponents,
            reference__exact=self.project.code
        ).values_list('internalKey', flat=True))

        Component.objects.bulk_create(
            [
                Component(
                    componentGroup=componentGroup,
                    internalKey=i,
                    code=i.upper(),
                    reference=self.project.code
                )
                for i in updatedComponents if i not in componentsList
            ]
        )

        ids = list(Component.objects.filter(
            componentGroup__code='PROJECT_COMPONENTS',
            internalKey__in=updatedComponents,
            reference__exact=self.project.code
        ).values_list('id', flat=True))

        self.project.components.clear()
        self.project.components.add(*ids)

        # TODO: Implement file upload via form.
        # TODO: Delete old file.
        if self.request.FILES.get('project-icon'):
            self.project.icon = self.request.FILES.get('project-icon')

        self.project.save()
