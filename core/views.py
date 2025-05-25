import operator
from functools import reduce
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.cache import cache
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.encoding import DjangoUnicodeDecodeError
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode

from core.forms import (
    LoginForm,
    RegistrationForm,
    ProfileForm,
    CustomSetPasswordForm,
    CustomPasswordResetForm,
    TeamForm,
    ProjectForm,
    BoardForm,
    LabelForm, ColumnForm, ColumnStatusForm
)
from core.models import (
    Profile,
    Team,
    Project,
    Board,
    Label,
    Column,
    Ticket
)
from taskmaster.operations import emailOperations


def loginView(request):
    if not request.session.session_key:
        request.session.save()

    if request.method == 'POST':
        uniqueVisitorId = request.session.session_key

        if cache.get(uniqueVisitorId) is not None and cache.get(uniqueVisitorId) > 3:
            cache.set(uniqueVisitorId, cache.get(uniqueVisitorId), 600)

            messages.error(
                request, 'Your account has been temporarily locked out because of too many failed login attempts.'
            )
            return redirect('core:login-view')

        form = LoginForm(request, request.POST)

        if form.is_valid():
            cache.delete(uniqueVisitorId)
            redirectUrl = request.GET.get('next')
            if redirectUrl:
                return redirect(redirectUrl)
            return redirect('core:index-view')

        if cache.get(uniqueVisitorId) is None:
            cache.set(uniqueVisitorId, 1)
        else:
            cache.incr(uniqueVisitorId, 1)

    else:
        form = LoginForm(request)

    context = {
        'form': form,
    }
    return render(request, 'core/login.html', context)


def registerView(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            newUser = form.save()
            emailOperations.sendEmailToActivateAccount(request, newUser)

            messages.info(
                request, 'We\'ve sent you an activation link. Please check your email.'
            )
            return redirect('core:login-view')
    else:
        form = RegistrationForm()

    context = {
        'form': form
    }
    return render(request, 'core/registration.html', context)


@login_required
def logoutView(request):
    logout(request)

    previousUrl = request.META.get('HTTP_REFERER')
    if previousUrl:
        return redirect(previousUrl)

    return redirect('core:login-view')


def activateAccountView(request, encodedId, token):
    try:
        uid = force_str(urlsafe_base64_decode(encodedId))
        user = User.objects.get(pk=uid)
    except (DjangoUnicodeDecodeError, ValueError, User.DoesNotExist):
        user = None

    passwordResetTokenGenerator = PasswordResetTokenGenerator()

    if user is not None and passwordResetTokenGenerator.check_token(user, token):
        user.is_active = True
        user.save()

        messages.success(
            request,
            'Account activated successfully'
        )
        return redirect('core:login-view')

    return render(request, 'core/activate-failed.html')


def forgotPasswordView(request):
    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data.get('email')

            try:
                user = User.objects.get(username=email)
            except User.DoesNotExist:
                user = None

            if user is not None:
                emailOperations.sendEmailToSetPassword(request, user)

            messages.info(
                request, 'Check your email for a password change link.'
            )
            return redirect('core:forgot-password-view')
    else:
        form = CustomPasswordResetForm()

    context = {
        'form': form
    }
    return render(request, 'core/forgot-password.html', context)


def setPasswordView(request, encodedId, token):
    try:
        uid = force_str(urlsafe_base64_decode(encodedId))
        user = User.objects.get(pk=uid)
    except (DjangoUnicodeDecodeError, ValueError, User.DoesNotExist):
        user = None

    passwordResetTokenGenerator = PasswordResetTokenGenerator()
    verifyToken = passwordResetTokenGenerator.check_token(user, token)

    if request.method == 'POST' and user is not None and verifyToken:
        form = CustomSetPasswordForm(user=user, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Your password has been updated successfully.'
            )
            return redirect('core:login-view')
    else:
        form = CustomSetPasswordForm(user=user)

    context = {
        'form': form,
    }
    TEMPLATE = 'set-password' if user is not None and verifyToken else 'activate-failed'
    return render(request, 'core/{}.html'.format(TEMPLATE), context)


@login_required
def profileView(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Profile updated successfully.'
            )
            return redirect('core:profile-view')
    else:
        form = ProfileForm(instance=profile)

    context = {
        'form': form,
    }
    return render(request, 'core/profile.html', context)


def indexView(request):
    pass


def dashboardView(request):
    pass


@login_required
def teamsView(request):
    if request.method == 'POST':
        form = TeamForm(request, request.POST)
        if form.is_valid():
            team = form.save()
            teamUrl = reverse('core:team-view', kwargs={'url': team.url})
            messages.success(
                request,
                f'Team created successfully! You can view it by clicking <a href="{teamUrl}">here</a>'
            )
            return redirect('core:teams-view')
    else:
        form = TeamForm(request)

    context = {
        'form': form,
        'teams': Team.objects.all().prefetch_related('admins', 'members')
    }
    return render(request, 'core/teams.html', context)


@login_required
def teamView(request, url):
    team = Team.objects.get(url=url)
    if not team.hasViewPermission(request.user):
        return HttpResponseForbidden('Forbidden')

    if request.method == 'POST':
        form = TeamForm(request, request.POST, instance=team)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Team updated successfully.'
            )
            return redirect('core:team-view', url=url)
    else:
        form = TeamForm(request, instance=team)

    context = {
        'form': form,
    }
    return render(request, 'core/team.html', context)


@login_required
def projectsView(request):
    if request.method == 'POST':
        form = ProjectForm(request, request.POST)
        if form.is_valid():
            project = form.save()
            projectUrl = reverse('core:project-view', kwargs={'url': project.url})
            messages.success(
                request,
                f'Project created successfully! You can view it by clicking <a href="{projectUrl}">here</a>'
            )
            return redirect('core:projects-view')
    else:
        form = ProjectForm(request)

    context = {
        'form': form,
        'projects': Project.objects.all().select_related('lead').prefetch_related('members')
    }
    return render(request, 'core/projects.html', context)


@login_required
def projectView(request, url):
    project = Project.objects.get(url=url)
    if not project.hasViewPermission(request.user):
        return HttpResponseForbidden('Forbidden')

    if request.method == 'POST':
        form = ProjectForm(request, request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Project updated successfully.'
            )
            return redirect('core:project-view', url=url)
    else:
        form = ProjectForm(request, instance=project)

    context = {
        'form': form,
    }
    return render(request, 'core/project.html', context)


@login_required
def boardsView(request):
    if request.method == 'POST':
        form = BoardForm(request, request.POST)
        if form.is_valid():
            board = form.save()
            boardUrl = reverse('core:board-view', kwargs={'url': board.url})
            messages.success(
                request,
                f'Board created successfully! You can view it by clicking <a href="{boardUrl}">here</a>'
            )
            return redirect('core:boards-view')
    else:
        form = BoardForm(request)

    context = {
        'form': form,
        'boards': Board.objects.all().select_related('project').prefetch_related('members', 'admins')
    }
    return render(request, 'core/boards.html', context)


@login_required
def boardView(request, url):
    board = Board.objects.prefetch_related('boardColumns__columnStatus__columnStatusTickets').get(url=url)
    columns = [c for c in board.boardColumns.all() if c.status not in [Column.Status.UNMAPPED, Column.Status.BACK_LOG]]
    context = {
        'board': board,
        'columns': columns,
    }
    return render(request, 'core/board.html', context)


@login_required
def boardSettingsView(request, url):
    tab = request.GET.get('tab')
    settingsUrl = reverse('core:board-settings-view', kwargs={'url': url})
    if not tab or tab not in ['general', 'columns']:
        return redirect(f"{settingsUrl}?{urlencode({'tab': 'general'})}")

    prefetchMapping = {
        'general': ['admins'],
        'columns': ['boardColumns__columnStatus__columnStatusTickets'],
    }
    board = Board.objects.prefetch_related(*prefetchMapping[tab]).get(url=url)
    if not board.hasViewPermission(request.user):
        return HttpResponseForbidden('Forbidden')

    context = {}
    templateName = f'core/board-settings-{tab}.html'
    redirectUrl = f"{settingsUrl}?{urlencode({'tab': tab})}"

    if tab == 'general':
        if request.method == 'POST':
            boardForm = BoardForm(request, request.POST, instance=board)
            if boardForm.is_valid():
                boardForm.save()
                messages.success(request, 'Board - General updated successfully.')
                return redirect(redirectUrl)
        else:
            boardForm = BoardForm(request, instance=board)
        context['form'] = boardForm

    elif tab == 'columns':
        columnForm = ColumnForm(board, request.POST if request.method == 'POST' else None)
        columnStatusForm = ColumnStatusForm(board, request.POST if request.method == 'POST' else None)

        if request.method == 'POST':
            if 'new-column' in request.POST:
                if columnForm.is_valid():
                    columnForm.save()
                    messages.success(request, 'Column created successfully.')
                    return redirect(redirectUrl)

            elif 'new-status' in request.POST:
                if columnStatusForm.is_valid():
                    columnStatusForm.save()
                    messages.success(request, 'Status created successfully.')
                    return redirect(redirectUrl)

        context.update({
            'board': board,
            'columnForm': columnForm,
            'columnStatusForm': columnStatusForm
        })
    return render(request, templateName, context)


@login_required
def labelsView(request):
    if request.method == 'POST':
        form = LabelForm(request.POST)
        if form.is_valid():
            label = form.save()
            labelUrl = reverse('core:label-view', kwargs={'url': label.name})
            messages.success(
                request,
                f'Label created successfully! You can view it by clicking <a href="{labelUrl}">here</a>'
            )
            return redirect('core:labels-view')
    else:
        form = LabelForm()

    context = {
        'form': form,
        'labels': Label.objects.all()
    }
    return render(request, 'core/labels.html', context)


@login_required
def labelView(request, url):
    label = Label.objects.get(url=url)
    if request.method == 'POST':
        form = LabelForm(request.POST, instance=label)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Label updated successfully.'
            )
            return redirect('core:label-view', url=url)
    else:
        form = LabelForm(instance=label)

    context = {
        'form': form,
    }
    return render(request, 'core/label.html', context)


def ticketsView(request):
    # todo: attributesToSearch, implement dropdown filters
    query = request.GET.get('query')
    relatedColumns = ['columnStatus__column', 'assignee', 'reporter']

    if query and query.strip():
        query = query.strip()
        attributesToSearch = [
            'url', 'summary', 'description', 'resolution', 'type', 'priority',
            'project__name', 'project__code', 'project__url', 'project__description', 'project__status',
            'assignee__first_name', 'assignee__last_name', 'reporter__first_name', 'reporter__last_name',
            'columnStatus__name', 'columnStatus__column__name', 'columnStatus__column__board__name',
            'columnStatus__column__board__type', 'columnStatus__column__status',
            'label__name', 'label__code', 'linkType'
        ]
        search_filter = Q()
        for field in attributesToSearch:
            search_filter |= Q(**{f'{field}__icontains': query})
        tickets = Ticket.objects.filter(search_filter).select_related(*relatedColumns).distinct()
    else:
        tickets = Ticket.objects.all().select_related(*relatedColumns)

    context = {
        'tickets': tickets,
    }
    return render(request, 'core/tickets.html', context)


def ticketView(request, url):
    pass


def backlogView(request, url):
    pass


def newTicketView(request):
    pass


def yourWorkView(request):
    pass
