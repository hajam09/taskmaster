from django import forms
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.contrib.auth.forms import (
    UserCreationForm,
    SetPasswordForm,
    PasswordResetForm
)
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Case, When, Max
from django.utils.safestring import mark_safe

from core.models import (
    Profile,
    Team,
    Project,
    Board,
    Label,
    Column,
    ColumnStatus,
    Sprint,
    Ticket
)


class LoginForm(forms.ModelForm):
    email = forms.EmailField(
        label=mark_safe('<strong>Email</strong>'),
        required=True,
        widget=forms.EmailInput(
            attrs={
                'class': 'form-control form-control-sm col'
            }
        )
    )
    password = forms.CharField(
        label=mark_safe('<strong>Password</strong>'),
        required=True,
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control form-control-sm col'
            }
        ),
        strip=False
    )

    class Meta:
        model = User
        fields = ('email', 'password')

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def clean_password(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        user = authenticate(username=email, password=password)
        if user:
            login(self.request, user)
            return self.cleaned_data

        raise ValidationError('Username or Password did not match!')


class RegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for key, value in self.fields.items():
            value.widget.attrs.update({'class': 'form-control form-control-sm col'})
            value.label = mark_safe(f'<strong>{value.label}</strong>')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('An account already exists for this email address!')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email']
        user.is_active = settings.DEBUG

        if commit:
            user.save()
        return user


class CustomSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key, value in self.fields.items():
            value.widget.attrs.update({'class': 'form-control form-control-sm col'})
            value.label = mark_safe(f'<strong>{value.label}</strong>')


class CustomPasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key, value in self.fields.items():
            value.widget.attrs.update({'class': 'form-control form-control-sm col'})
            value.label = mark_safe(f'<strong>{value.label}</strong>')


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('jobTitle', 'department')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for key, value in self.fields.items():
            value.widget.attrs.update({'class': 'form-control form-control-sm col'})
            value.label = mark_safe(f'<strong>{value.label}</strong>')


class TeamForm(forms.ModelForm):
    visibility = forms.ChoiceField(
        label=mark_safe('<strong>Visibility</strong>'),
        required=True,
        choices=[('EVERYONE', 'Everyone'), ('MEMBERS', 'Members')],
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input',
            'style': 'height: 34px; width: 34px',
        })
    )

    class Meta:
        model = Team
        fields = ['name', 'description', 'admins', 'members', 'visibility']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control form-control-sm col'}),
            'description': forms.Textarea(attrs={'class': 'form-control form-control-sm col', 'rows': 5}),
            'admins': forms.SelectMultiple(attrs={
                'class': 'form-control form-control-sm col select2bs4',
                'style': 'width: 100%',
                'multiple': 'multiple',
            }),
            'members': forms.SelectMultiple(attrs={
                'class': 'form-control form-control-sm col select2bs4',
                'style': 'width: 100%',
                'multiple': 'multiple',
            }),
        }
        labels = {
            'name': mark_safe('<strong>Name</strong>'),
            'description': mark_safe('<strong>Description</strong>'),
            'admins': mark_safe('<strong>Admins</strong>'),
            'members': mark_safe('<strong>Members</strong>'),
        }

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        if getattr(self.instance, 'id'):
            self.fields['visibility'].initial = 'MEMBERS' if self.instance.isPrivate else 'EVERYONE'
            self.hasEditPermission = request.user in self.instance.admins.all()

            if not self.hasEditPermission:
                for field in self.fields.values():
                    field.widget.attrs['disabled'] = True

    def clean(self):
        cleaned_data = super().clean()
        visibility = cleaned_data.get('visibility')
        cleaned_data['isPrivate'] = visibility == 'MEMBERS'
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.isPrivate = self.cleaned_data.get('visibility') == 'MEMBERS'
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class ProjectForm(forms.ModelForm):
    visibility = forms.ChoiceField(
        label=mark_safe('<strong>Visibility</strong>'),
        required=True,
        choices=[('EVERYONE', 'Everyone'), ('MEMBERS', 'Members')],
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input',
            'style': 'height: 34px; width: 34px',
        })
    )

    class Meta:
        model = Project
        fields = ['name', 'code', 'description', 'startDate', 'endDate', 'status', 'members', 'visibility']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control form-control-sm col'}),
            'code': forms.TextInput(attrs={'class': 'form-control form-control-sm col'}),
            'description': forms.Textarea(attrs={'class': 'form-control form-control-sm col', 'rows': 5}),
            'startDate': forms.DateInput(attrs={'class': 'form-control form-control-sm col', 'type': 'date'}),
            'endDate': forms.DateInput(attrs={'class': 'form-control form-control-sm col', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-control form-control-sm col'}),
            'members': forms.SelectMultiple(attrs={
                'class': 'form-control form-control-sm col select2bs4',
                'style': 'width: 100%',
                'multiple': 'multiple',
            }),
        }
        labels = {
            'name': mark_safe('<strong>Name</strong>'),
            'code': mark_safe('<strong>Code</strong>'),
            'description': mark_safe('<strong>Description</strong>'),
            'startDate': mark_safe('<strong>Start Date</strong>'),
            'endDate': mark_safe('<strong>End Date</strong>'),
            'status': mark_safe('<strong>Status</strong>'),
            'members': mark_safe('<strong>Members</strong>'),
        }

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.fields['status'].choices = [(None, '---------')] + Project.Status.choices

        if getattr(self.instance, 'id'):
            self.fields['visibility'].initial = 'MEMBERS' if self.instance.isPrivate else 'EVERYONE'
            self.hasEditPermission = request.user == self.instance.lead or request.user in self.instance.members.all()

            if not self.hasEditPermission:
                for field in self.fields.values():
                    field.widget.attrs['disabled'] = True

    def clean(self):
        cleaned_data = super().clean()
        visibility = cleaned_data.get('visibility')
        cleaned_data['isPrivate'] = visibility == 'MEMBERS'
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.isPrivate = self.cleaned_data.get('visibility') == 'MEMBERS'
        instance.lead = self.request.user
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class BoardForm(forms.ModelForm):
    visibility = forms.ChoiceField(
        label=mark_safe('<strong>Visibility</strong>'),
        required=True,
        choices=[('EVERYONE', 'Everyone'), ('MEMBERS', 'Members')],
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input',
            'style': 'height: 34px; width: 34px',
        })
    )

    class Meta:
        model = Board
        fields = ['name', 'type', 'project', 'admins', 'members', 'visibility']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control form-control-sm col'}),
            'type': forms.Select(attrs={'class': 'form-control form-control-sm col'}),
            'project': forms.Select(attrs={'class': 'form-control form-control-sm col'}),
            'admins': forms.SelectMultiple(attrs={
                'class': 'form-control form-control-sm col select2bs4',
                'style': 'width: 100%',
                'multiple': 'multiple',
            }),
            'members': forms.SelectMultiple(attrs={
                'class': 'form-control form-control-sm col select2bs4',
                'style': 'width: 100%',
                'multiple': 'multiple',
            }),
        }
        labels = {
            'name': mark_safe('<strong>Name</strong>'),
            'type': mark_safe('<strong>Type</strong>'),
            'project': mark_safe('<strong>Project</strong>'),
            'admins': mark_safe('<strong>Admins</strong>'),
            'members': mark_safe('<strong>Members</strong>'),
        }

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.fields['type'].choices = [(None, '---------')] + Board.Types.choices
        self.fields['type'].initial = None

        if getattr(self.instance, 'id'):
            self.fields['visibility'].initial = 'MEMBERS' if self.instance.isPrivate else 'EVERYONE'
            self.hasEditPermission = request.user in self.instance.admins.all()

            if not self.hasEditPermission:
                for field in self.fields.values():
                    field.widget.attrs['disabled'] = True

    def clean(self):
        cleaned_data = super().clean()
        visibility = cleaned_data.get('visibility')
        cleaned_data['isPrivate'] = visibility == 'MEMBERS'
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.isPrivate = self.cleaned_data.get('visibility') == 'MEMBERS'
        isBoardNew = getattr(self.instance, 'id') is None
        if commit:
            instance.save()
            self.save_m2m()

        if isBoardNew:
            unmapped = Column(name='Unmapped', board=instance, status=Column.Status.UNMAPPED)
            backLog = Column(name='Back Log', board=instance, status=Column.Status.BACK_LOG)
            todo = Column(name='To Do', board=instance, status=Column.Status.TODO)
            inProgress = Column(name='In Progress', board=instance, status=Column.Status.IN_PROGRESS)
            done = Column(name='Done', board=instance, status=Column.Status.DONE)
            columns = Column.objects.bulk_create([unmapped, backLog, todo, inProgress, done])
            for c in columns:
                c.orderNo = c.id
            Column.objects.bulk_update(columns, ['orderNo'])

            status = ColumnStatus.objects.bulk_create([
                ColumnStatus(name='Back Log', column=backLog),
                ColumnStatus(name='To Do', column=todo),
                ColumnStatus(name='In Progress', column=inProgress),
                ColumnStatus(name='Done', column=done)
            ])
            for s in status:
                s.orderNo = s.id
            ColumnStatus.objects.bulk_update(columns, ['orderNo'])
        return instance


class LabelForm(forms.ModelForm):
    class Meta:
        model = Label
        fields = ('name', 'code', 'colour')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if getattr(self.instance, 'id'):
            self.fields['colour'].initial = self.instance.colour

        for key, value in self.fields.items():
            value.widget.attrs.update({'class': 'form-control form-control-sm col'})
            value.label = mark_safe(f'<strong>{value.label}</strong>')


class ColumnForm(forms.ModelForm):
    class Meta:
        model = Column
        fields = ('name', 'status')

    def __init__(self, board, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.board = board
        self.fields['status'].choices = [(None, '---------')] + Column.Status.choices[2:]
        self.fields['status'].initial = None

        if getattr(self.instance, 'id'):
            pass

        for key, value in self.fields.items():
            value.widget.attrs.update({'class': 'form-control form-control-sm col'})
            value.label = mark_safe(f'<strong>{value.label}</strong>')

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.board = self.board
        if commit:
            instance.save()
        return instance


class ColumnStatusForm(forms.ModelForm):
    class Meta:
        model = ColumnStatus
        fields = ('name', 'column')

    def __init__(self, board, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['column'].queryset = board.boardColumns.all()
        self.fields['column'].initial = None
        self.fields['column'].empty_label = '---------'

        if getattr(self.instance, 'id'):
            pass

        for key, value in self.fields.items():
            value.widget.attrs.update({'class': 'form-control form-control-sm col'})
            value.label = mark_safe(f'<strong>{value.label}</strong>')


class SprintForm(forms.ModelForm):
    class Meta:
        model = Sprint
        fields = ('name', 'startDate', 'endDate', 'goal')

    def __init__(self, board, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.board = board
        self.fields['name'].initial = f'{board.name} Sprint {Sprint.objects.filter(board=board).count() + 1}'

        for key, value in self.fields.items():
            value.widget.attrs.update({'class': 'form-control form-control-sm col'})
            value.label = mark_safe(f'<strong>{value.label}</strong>')

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.board = self.board
        if commit:
            instance.save()
        return instance


class TicketForm(forms.ModelForm):
    board = forms.ModelChoiceField(
        queryset=Board.objects.none(),
        required=True,
        label='Board',
        widget=forms.Select(),
        empty_label='---------'
    )
    assignee = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        label='Assignee',
        widget=forms.Select(),
        empty_label='---------'
    )

    class Meta:
        model = Ticket
        fields = ('summary', 'description', 'type', 'priority', 'board', 'storyPoints', 'assignee', 'resolution')

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.fields['board'].queryset = Board.objects.all()

        users = list(User.objects.values_list('id', flat=True))
        users.remove(self.request.user.id)
        users.insert(0, self.request.user.id)
        preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(users)])
        self.fields['assignee'].queryset = User.objects.filter(id__in=users).order_by(preserved)

        for key, value in self.fields.items():
            value.widget.attrs.update({'class': 'form-control form-control-sm col'})
            value.label = mark_safe(f'<strong>{value.label}</strong>')

    def save(self, commit=True):
        instance = super().save(commit=False)

        board = self.cleaned_data.get('board')
        instance.url = f'{board.project.code}-{Ticket.objects.filter(project=board.project).count() + 3}'
        instance.project = board.project
        instance.reporter = self.request.user
        instance.columnStatus = ColumnStatus.objects.filter(
            column__board=board,
            column__status=Column.Status.BACK_LOG
        ).first()

        if commit:
            instance.save()
            self.save_m2m()
        return instance
