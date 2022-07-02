import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.db.models import Q
from django.http import Http404
from django.shortcuts import render

from accounts.models import Profile, Component, Team, ComponentGroup
from jira.models import Board, Project, Column, Ticket, TicketAttachment, Label
from taskmaster.operations import databaseOperations


def index(request):
    pass


def dashboard(request):
    pass


def teams(request):
    pass


@login_required
def team(request, url):
    # TODO: Add admins and members to the team.
    try:
        thisTeam = Team.objects.prefetch_related('members__profile').get(url=url)
    except Team.DoesNotExist:
        raise Http404

    if not thisTeam.hasAccessPermission(request.user):
        raise PermissionDenied()

    allProfiles = Profile.objects.all().select_related('user')
    excludedMembers = allProfiles.exclude(user__id__in=[i.id for i in thisTeam.members.all()])
    excludedAdmins = allProfiles.exclude(user__id__in=[i.id for i in thisTeam.admins.all()])

    context = {
        "team": thisTeam,
        "members": excludedMembers,
        "admins": excludedAdmins,
    }
    return render(request, "jira/team.html", context)


def peopleAndTeamSearch(request):
    pass


def profileView(request, url):
    pass


def ticketDetailView(request, internalKey):
    """
    TODO: remove unused css on the ticket css files
    TODO: Try to move the components to external files and import it.
    TODO: Fix spacing on the texts.
    TODO: Implement the comment section.
    TODO: Fix linked issue component.
    TODO: Fix the style for right divs.
    TODO: Collapse items
    TODO: Fix file attachment style
    TODO: Allow file attachment delete option
    """
    try:
        ticket = Ticket.objects.get(internalKey__iexact=internalKey)
    except Ticket.DoesNotExist:
        raise Http404

    ticketIssueTypes = Component.objects.filter(componentGroup__code="TICKET_ISSUE_TYPE")
    ticketPriorities = Component.objects.filter(componentGroup__code="TICKET_PRIORITY")
    projectComponents = Component.objects.filter(componentGroup__code="PROJECT_COMPONENTS", reference__exact=f"Component_{ticket.project.code}")
    allProfiles = Profile.objects.all().select_related('user')

    if request.method == "POST":
        ticket.summary = request.POST['summary']
        ticket.description = request.POST['description']
        ticket.fixVersion = request.POST['fixVersion']
        # ticket.component = request.POST['component'] # multiple values
        ticket.assignee = databaseOperations.getObjectByIdOrNone([i.user for i in allProfiles],
                                                                 request.POST['assignee'])
        ticket.storyPoints = request.POST['storyPoints']
        # ticket.manDays = request.POST['manDays']
        ticket.issueType = databaseOperations.getObjectByIdOrNone(ticketIssueTypes, request.POST['ticketIssueType'])
        ticket.priority = databaseOperations.getObjectByIdOrNone(ticketPriorities, request.POST['priority'])

        ticket.label.clear()
        ticket.label.add(*request.POST.getlist('labels'))

        TicketAttachment.objects.bulk_create(
            TicketAttachment(
                ticket=ticket,
                internalKey=attachment.name,
                attachment=attachment
            )
            for attachment in request.FILES.getlist('attachments')
        )
        ticket.save()

    ticketComments = [
        {
            'id': i.pk,
            'creator': i.creator.get_full_name(),
            'comment': i.comment.replace("\n", "<br />"),
            'edited': i.edited,
            'likeCount': i.likes.count(),
            'dislikeCount': i.dislikes.count(),
            'canEdit': i.creator == request.user,
            'masterCommentId': i.reply.pk if i.reply else None
        }
        for i in ticket.ticketComments.all()
    ]

    epicTickets = [
        {
            'id': i.pk,
            'internalKey': i.internalKey,
            'summary': i.summary,
            'url': i.getTicketUrl(),
            'assignee': {
                'id': i.assignee.pk,
                'fullName': i.assignee.get_full_name(),
                'icon': i.assignee.profile.profilePicture.url
            } if i.assignee is not None else {},
            'issueType': {
                'id': i.issueType.pk,
                'icon': i.issueType.icon,
                'internalKey': i.issueType.internalKey
            },
            'priority': {
                'id': i.priority.pk,
                'icon': i.priority.icon,
                'internalKey': i.priority.internalKey
            }
        }
        for i in ticket.epicTickets.all().order_by('orderNo')
    ]

    subTaskTickets = [
        {
            'id': i.pk,
            'internalKey': i.internalKey,
            'summary': i.summary,
            'url': i.getTicketUrl(),
            'assignee': {
                'id': i.assignee.pk,
                'fullName': i.assignee.get_full_name(),
                'icon': i.assignee.profile.profilePicture.url
            } if i.assignee is not None else {},
            'issueType': {
                'id': i.issueType.pk,
                'icon': i.issueType.icon,
                'internalKey': i.issueType.internalKey
            },
            'priority': {
                'id': i.priority.pk,
                'icon': i.priority.icon,
                'internalKey': i.priority.internalKey
            }
        }
        for i in ticket.subTask.all().order_by('orderNo')
    ]

    context = {
        "ticket": ticket,
        "allProfiles": allProfiles,
        "ticketIssueTypes": ticketIssueTypes,
        "ticketPriorities": ticketPriorities,
        "projectComponents": projectComponents,
        "ticketComments": json.dumps(ticketComments),
        "epicTickets": json.dumps(epicTickets),
        "subTaskTickets": json.dumps(subTaskTickets),
    }
    return render(request, "jira/ticketDetailViewPage.html", context)


@login_required
def boards(request):
    """
       TODO: Allow user to copy board on template and make changes before creating new board.
       TODO: Inform that in some places the project will appear to other users.
    """
    allBoards = Board.objects.all().prefetch_related('projects', 'admins', 'members')
    allProfiles = Profile.objects.all().select_related('user')
    allProjects = Project.objects.filter(Q(isPrivate=True, members__in=[request.user]) | Q(isPrivate=False))

    if request.method == "POST":
        boardAdmins = [i.user for i in allProfiles if str(i.user.pk) in request.POST.getlist('board-admins')]
        boardMembers = [i.user for i in allProfiles if str(i.user.pk) in request.POST.getlist('board-members')]
        boardProjects = [i for i in allProjects if str(i.pk) in request.POST.getlist('board-projects')]

        try:
            newBoard = Board.objects.create(
                internalKey=request.POST['board-name'],
                isPrivate=request.POST['board-visibility'] == 'visibility-members'
            )

            # mandatory columns for a board
            Column.objects.bulk_create(
                [
                    Column(board=newBoard, internalKey='BACKLOG', colour='#42526e', orderNo=1),
                    Column(board=newBoard, internalKey='TO DO', colour='#42526e', orderNo=2),
                    Column(board=newBoard, internalKey='IN PROGRESS', colour='#0052cc', orderNo=3),
                    Column(board=newBoard, internalKey='DONE', colour='#00875a', orderNo=4)
                ]
            )

            newBoard.projects.add(*boardProjects)
            newBoard.members.add(*boardMembers)
            newBoard.admins.add(*boardAdmins)

            allBoards = Board.objects.all().prefetch_related('projects', 'admins', 'members')
        except IntegrityError:
            messages.error(
                request,
                f'Board with name {request.POST["board-name"]} already exists.'
            )

    context = {
        'projects': allProjects,
        'profiles': allProfiles,
        'boards': allBoards,
    }
    return render(request, 'jira/boards.html', context)


@login_required
def boardSettings(request, url):
    try:
        thisBoard = Board.objects.prefetch_related('boardColumns', 'boardLabels').get(url=url)
    except Board.DoesNotExist:
        raise Http404

    allProjects = Project.objects.filter(Q(isPrivate=True, members__in=[request.user]) | Q(isPrivate=False))
    allProfiles = Profile.objects.all().select_related('user')

    context = {
        'board': thisBoard,
        'projects': allProjects,
        'profiles': allProfiles
    }
    return render(request, 'jira/boardSettings.html', context)


@login_required
def board(request, url):
    try:
        thisBoard = Board.objects.get(url=url)
    except Board.DoesNotExist:
        raise Http404

    if not thisBoard.hasAccessPermission(request.user):
        # TODO: Show access denied page.
        raise PermissionDenied()

    context = {

        "board": thisBoard
    }
    return render(request, "jira/board.html", context)


def backlog(request, url):
    # url = boardUrl
    pass


def yourWork(request):
    pass


@login_required
def projects(request):
    """
    TODO: Filter dropdown to filter projects by name, name contains, lead, status (show ongoing and terminated)...
    """
    projectQuery = Q(isPrivate=True, members__in=[request.user]) | Q(isPrivate=False)
    allProjects = Project.objects.filter(projectQuery).select_related('status', 'lead')
    allProfiles = Profile.objects.all().select_related('user')

    if request.method == "POST":
        newProject = Project()
        newProject.internalKey = request.POST['project-name']
        newProject.code = request.POST['project-code']
        newProject.description = request.POST['project-description']
        newProject.lead = request.user
        newProject.isPrivate = request.POST['project-visibility'] == 'visibility-members'
        newProject.status = Component.objects.get(componentGroup__code='PROJECT_STATUS', code='ON_GOING')

        if request.FILES.get('project-icon'):
            newProject.icon = request.FILES.get('project-icon')

        if request.POST['project-start']:
            newProject.startDate = request.POST['project-start']

        if request.POST['project-due']:
            newProject.endDate = request.POST['project-due']

        newProject.save()
        newProject.members.add(*request.POST.getlist('project-users', []))
        allProjects = Project.objects.filter(projectQuery).select_related('status', 'lead')

    context = {
        'projects': allProjects,
        'profiles': allProfiles
    }
    return render(request, 'jira/projects.html', context)


def project(request, url):
    # url = project code
    pass


def projectSettings(request, url):
    # Create Component
    try:
        thisProject = Project.objects.get(url=url)
    except Project.DoesNotExist:
        raise Http404

    allProfiles = Profile.objects.all().select_related('user')
    component = Component.objects.filter(componentGroup__code='PROJECT_STATUS')

    if request.method == "POST":
        thisProject.internalKey = request.POST['project-name']
        thisProject.description = request.POST['project-description']
        thisProject.lead = next(p.user for p in allProfiles if str(p.user.id) == request.POST['project-lead'])
        thisProject.startDate = request.POST['project-start']
        thisProject.endDate = request.POST['project-end']
        thisProject.status = databaseOperations.getObjectByIdOrNone(component, request.POST['project-status'])
        thisProject.isPrivate = request.POST['project-visibility'] == 'visibility-members'

        if request.FILES.get('project-icon'):
            thisProject.icon = request.FILES.get('project-icon')

        updatedProjectMembers = [
            i.user for i in allProfiles if str(i.user.id) in request.POST.getlist('project-members')
        ]
        thisProject.members.clear()
        thisProject.members.add(*updatedProjectMembers)
        thisProject.save()

    context = {
        'project': thisProject,
        'profiles': allProfiles,
        'projectStatusComponent': component
    }
    return render(request, 'jira/projectSettings.html', context)


def projectIssues(request, url):
    pass


def profileAndSettings(request):
    pass


def projectBacklog(request, projectId):
    pass
