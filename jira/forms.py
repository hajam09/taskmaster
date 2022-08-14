from datetime import datetime

from django import forms
from django.core.cache import cache

from accounts.models import Profile, ComponentGroup, Component


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
            (str(i.internalKey), i.internalKey) for i in cache.get('PROJECT_COMPONENTS')
            if i.reference == self.project.code
        ]
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

        newComponents = Component.objects.bulk_create(
            [
                Component(
                    componentGroup=componentGroup,
                    internalKey=i,
                    reference=self.project.code
                )
                for i in updatedComponents if i not in componentsList
            ]
        )

        updatedComponents += [i.internalKey for i in newComponents]

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
