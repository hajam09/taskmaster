import json
import re
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.db.models import Q
from django.http import Http404
from django.shortcuts import render, redirect

from accounts.models import Profile, Component, Team, ComponentGroup
from jira.models import Board, Project, Column, Ticket, TicketAttachment, TicketComment
from taskmaster.operations import databaseOperations, emailOperations

cache.set('TICKET_ISSUE_TYPE', Component.objects.filter(componentGroup__code='TICKET_ISSUE_TYPE'), None)
cache.set('PROJECT_COMPONENTS', Component.objects.filter(componentGroup__code='PROJECT_COMPONENTS'), None)
cache.set('PROJECT_STATUS', Component.objects.filter(componentGroup__code='PROJECT_STATUS'), None)
cache.set('TICKET_PRIORITY', Component.objects.filter(componentGroup__code='TICKET_PRIORITY'), None)
cache.set('TICKET_RESOLUTIONS', Component.objects.filter(componentGroup__code='TICKET_RESOLUTIONS'), None)
cache.set('FILE_ICONS', Component.objects.filter(componentGroup__code='FILE_ICONS'), None)


def index(request):
    pass


def dashboard(request):
    projectComponents = cache.get('PROJECT_COMPONENTS').prefetch_related('ticketComponents__issueType', 'ticketComponents__priority')
    ticketIssueType = cache.get('TICKET_ISSUE_TYPE')
    ticketPriority = cache.get('TICKET_PRIORITY')
    componentListByIssueType = []
    componentListByPriority = []

    for component in projectComponents:
        tickets = component.ticketComponents.all()
        ticketCounterForIssueCode = {}
        ticketCounterForPriority = {}

        for issue in ticketIssueType:
            ticketCounterForIssueCode[issue.code] = {
                'id': issue.id,
                'internalKey': issue.internalKey,
                'icon': issue.icon,
                'count': len([i for i in tickets if i.issueType.code == issue.code])
            }

        for priority in ticketPriority:
            ticketCounterForPriority[priority.code] = {
                'id': priority.id,
                'internalKey': priority.internalKey,
                'icon': priority.icon,
                'count': len([i for i in tickets if i.priority.code == priority.code])
            }

        componentListByIssueType.append({
            'id': component.id,
            'internalKey': component.internalKey,
            'issueCounter': ticketCounterForIssueCode,
            'total': len(tickets)
        })

        componentListByPriority.append({
            'id': component.id,
            'internalKey': component.internalKey,
            'issueCounter': ticketCounterForPriority,
            'total': len(tickets)
        })

    context = {
        'componentListByIssueType': componentListByIssueType,
        'componentListByPriority': componentListByPriority,
        'ticketIssueType': ticketIssueType,
        'ticketPriority': ticketPriority,
    }
    return render(request, "jira/dashboard.html", context)


def teams(request):
    allTeams = Team.objects.all().prefetch_related('admins', 'members')
    allProfiles = Profile.objects.all().select_related('user')

    if request.method == "POST":
        try:
            newTeam = Team.objects.create(
                internalKey=request.POST['team-name'],
                description=request.POST['team-description'],
                isPrivate=request.POST['team-visibility'] == 'visibility-members'
            )

            newTeam.members.add(*request.POST.getlist('team-members'))
            newTeam.admins.add(*request.POST.getlist('team-admins'))

            allTeams = Team.objects.all().prefetch_related('admins', 'members')
        except IntegrityError:
            messages.error(
                request,
                f'Team with name {request.POST["team-name"]} already exists.'
            )

    context = {
        'teams': allTeams,
        'profiles': allProfiles,
    }
    return render(request, "jira/teams.html", context)


@login_required
def team(request, url):
    # TODO/Story: Record team/user activity session and display.
    try:
        thisTeam = Team.objects.prefetch_related('members__profile').get(url=url)
    except Team.DoesNotExist:
        raise Http404

    if not thisTeam.hasAccessPermission(request.user):
        raise PermissionDenied()

    allProfiles = Profile.objects.all().select_related('user')
    excludedMembers = allProfiles.exclude(user__id__in=[i.id for i in thisTeam.members.all()])
    excludedAdmins = allProfiles.exclude(user__id__in=[i.id for i in thisTeam.admins.all()])

    if request.method == "POST":
        teamAdmins = request.POST.getlist('team-admins')
        teamMembers = request.POST.getlist('team-members')
        thisTeam.admins.add(*teamAdmins)
        thisTeam.members.add(*teamMembers)

        for user in set(thisTeam.admins.filter(id__in=teamAdmins) | thisTeam.members.filter(id__in=teamMembers)):
            emailOperations.sendEmailToNotifyUserAddedToTeam(request, user)

    context = {
        "team": thisTeam,
        "members": excludedMembers,
        "admins": excludedAdmins,
        "associates": set(thisTeam.admins.all() | thisTeam.members.all())
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
        ticket = Ticket.objects.select_related(
            'project',
            'issueType',
            'resolution',
            'column',
            'priority',
            'assignee__profile', 'reporter__profile'
        ).prefetch_related('label', 'component', 'watchers').get(internalKey__iexact=internalKey)
    except Ticket.DoesNotExist:
        raise Http404

    if request.method == "POST":
        allProfiles = Profile.objects.all().select_related('user')

        ticket.summary = request.POST['summary']
        ticket.description = request.POST['description']
        ticket.fixVersion = request.POST['fixVersion']
        ticket.storyPoints = request.POST['storyPoints']

        ticket.assignee = databaseOperations.getObjectByIdOrNone([i.user for i in allProfiles], request.POST['assignee'])
        ticket.issueType = databaseOperations.getObjectByIdOrNone(cache.get('TICKET_ISSUE_TYPE'), request.POST['ticketIssueType'])
        ticket.priority = databaseOperations.getObjectByIdOrNone(cache.get('TICKET_PRIORITY'), request.POST['priority'])

        ticket.component.clear()
        ticket.component.add(*request.POST.getlist('components'))

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

    def getWatchersMessage():
        if not request.user.is_authenticated:
            return "You have to be logged in to watch an issue."
        if request.user in ticket.watchers.all():
            return "You are watching this issue. Click to stop watching this issue."
        return "You are not watching this issue. Click to watch this issue."

    ticketDetails = {
        'id': ticket.id,
        'internalKey': ticket.internalKey,
        'summary': ticket.summary,
        'description': ticket.description,
        'createdDate': datetime.strftime(ticket.createdDttm, '%d/%B/%Y, %I:%M %p'),
        'modifiedDate': datetime.strftime(ticket.modifiedDttm, '%d/%B/%Y, %I:%M %p'),
        'link': ticket.getTicketUrl(),
        'storyPoints': ticket.storyPoints,
        'fixVersion': ticket.fixVersion or '',
        'project': {
            'id': ticket.project.id,
            'internalKey': ticket.project.internalKey,
            'code': ticket.project.code,
            'icon': ticket.project.icon.url,
            'link': ticket.project.getUrl()
        },
        'labels': [
            {
                'id': label.id,
                'internalKey': label.internalKey,
                'colour': label.colour,
            }
            for label in ticket.label.all()
        ],
        'components': [
            {
                'id': component.id,
                'internalKey': component.internalKey,
                'code': component.code,
            }
            for component in ticket.component.all()
        ],
        'issueType': {
            'internalKey': ticket.issueType.internalKey,
            'code': ticket.issueType.code,
            'icon': ticket.issueType.icon,
        },
        'resolution': {
            'internalKey': ticket.resolution.internalKey,
        },
        'column': {
            'internalKey': ticket.column.internalKey,
            'colour': ticket.column.colour,
        },
        'priority': {
            'internalKey': ticket.priority.internalKey,
            'code': ticket.priority.code,
            'icon': ticket.priority.icon
        },
        'assignee': {
            'id': ticket.assignee.pk,
            'fullName': ticket.assignee.get_full_name(),
            'icon': ticket.assignee.profile.profilePicture.url
        } if ticket.assignee is not None else {},
        'reporter': {
            'id': ticket.reporter.pk,
            'fullName': ticket.reporter.get_full_name(),
            'icon': ticket.reporter.profile.profilePicture.url
        } if ticket.reporter is not None else {},
        'watchers': {
            'counter': ticket.watchers.count(),
            'isWatching': "true" if request.user in ticket.watchers.all() else "false",
            'message': getWatchersMessage(),
        }
    }
    context = {
        'ticket': ticketDetails
    }
    return render(request, "jira/ticketDetailViewPage.html", context)


@login_required
def boards(request):
    allBoards = Board.objects.all().prefetch_related('projects', 'admins', 'members')
    allProfiles = Profile.objects.all().select_related('user')
    allProjects = Project.objects.filter(Q(isPrivate=True, members__in=[request.user]) | Q(isPrivate=False)).distinct()

    if request.method == "POST":
        try:
            newBoard = Board.objects.create(
                internalKey=request.POST['board-name'],
                type=request.POST['board-type'],
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

            newBoard.projects.add(*request.POST.getlist('board-projects'))
            newBoard.members.add(*request.POST.getlist('board-members'))
            newBoard.admins.add(*request.POST.getlist('board-admins'))

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
    """
    TODO: Only admins can edit.
    // Contact a TaskMaster or the board administrator to configure this board
    """
    try:
        thisBoard = Board.objects.prefetch_related('boardColumns', 'boardLabels').get(url=url)
    except Board.DoesNotExist:
        raise Http404

    allProjects = Project.objects.filter(Q(isPrivate=True, members__in=[request.user]) | Q(isPrivate=False)).distinct()
    allProfiles = Profile.objects.all().select_related('user')

    context = {
        'board': thisBoard,
        'projects': allProjects,
        'profiles': allProfiles
    }
    return render(request, 'jira/boardSettings.html', context)


@login_required
def board(request, url):
    """
    TODO: Remove unused css files from kanbanBoardCSS1-5
    """
    try:
        thisBoard = Board.objects.get(url=url)
    except Board.DoesNotExist:
        raise Http404

    if not thisBoard.hasAccessPermission(request.user):
        raise PermissionDenied()

    if thisBoard.type == "KANBAN":
        TEMPLATE = "jira/kanbanBoard.html"
    else:
        TEMPLATE = "jira/scrumBoard.html"

    context = {
        "board": thisBoard,
    }
    return render(request, TEMPLATE, context)


def backlog(request, url):
    try:
        thisBoard = Board.objects.get(url=url)
    except Board.DoesNotExist:
        raise Http404

    if not thisBoard.hasAccessPermission(request.user):
        raise PermissionDenied()

    if thisBoard.type == "KANBAN":
        TEMPLATE = "jira/kanbanBacklog.html"
        columns = thisBoard.boardColumns.all()
        activeAndInActive = {
            "active": next((c for c in columns if c.internalKey == "TO DO")),
            "inActive": next((c for c in columns if c.internalKey == "BACKLOG")),
        }

    else:
        TEMPLATE = "jira/scrumBacklog.html"
        activeAndInActive = {}

    context = {
        "board": thisBoard,
        "columns": activeAndInActive
    }
    return render(request, TEMPLATE, context)


def yourWork(request):
    pass


@login_required
def projects(request):
    projectQuery = Q(isPrivate=True, members__in=[request.user]) | Q(isPrivate=False)
    allProjects = Project.objects.filter(projectQuery).distinct().select_related('status', 'lead')
    allProfiles = Profile.objects.all().select_related('user')

    if request.method == "POST":
        try:
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
            allProjects = Project.objects.filter(projectQuery).distinct().select_related('status', 'lead')
        except IntegrityError:
            messages.error(
                request,
                f'Project with code {request.POST["project-code"]} already exists.'
            )

    context = {
        'allProjects': allProjects,
        'profiles': allProfiles
    }
    return render(request, 'jira/projects.html', context)


def project(request, url):
    # to issuesListView
    try:
        thisProject = Project.objects.get(url=url)
    except Project.DoesNotExist:
        raise Http404

    context = {
        'project': thisProject,
    }
    return render(request, 'jira/project.html', context)


def projectSettings(request, url):
    try:
        thisProject = Project.objects.get(url=url)
    except Project.DoesNotExist:
        raise Http404

    allProfiles = Profile.objects.all().select_related('user')
    projectStatusComponent = Component.objects.filter(componentGroup__code='PROJECT_STATUS')
    projectComponents = Component.objects.filter(componentGroup__code='PROJECT_COMPONENTS', reference__exact=thisProject.code)

    if request.method == "POST":
        thisProject.internalKey = request.POST['project-name']
        thisProject.description = request.POST['project-description']
        thisProject.lead = next(p.user for p in allProfiles if str(p.user.id) == request.POST['project-lead'])
        thisProject.startDate = datetime.strptime(request.POST['project-start'], "%Y-%m-%d").date()
        thisProject.endDate = datetime.strptime(request.POST['project-end'], "%Y-%m-%d").date()
        thisProject.status = databaseOperations.getObjectByIdOrNone(projectStatusComponent, request.POST['project-status'])
        thisProject.isPrivate = request.POST['project-visibility'] == 'visibility-members'

        if request.FILES.get('project-icon'):
            thisProject.icon = request.FILES.get('project-icon')

        thisProject.members.clear()
        thisProject.members.add(*request.POST.getlist('project-members'))
        componentGroup = ComponentGroup.objects.get(code='PROJECT_COMPONENTS')

        Component.objects.bulk_create(
            [
                Component(
                    componentGroup=componentGroup,
                    internalKey=i,
                    code=i.upper(),
                    reference=thisProject.code
                )
                for i in request.POST.getlist('project-components') if re.search('[a-zA-Z]', i)
            ]
        )
        thisProject.save()

    context = {
        'project': thisProject,
        'profiles': allProfiles,
        'projectStatusComponent': projectStatusComponent,
        'projectComponents': projectComponents,
    }
    return render(request, 'jira/projectSettings.html', context)


def projectIssues(request, url):
    try:
        thisProject = Project.objects.get(url=url)
    except Project.DoesNotExist:
        raise Http404

    context = {
        'project': thisProject,
    }
    pass


def issuesListView(request):
    # TODO/Improvement: Move this to API.
    # TODO/Improvement: Dynamically add filter based on url search query parameter.
    allTickets = Ticket.objects.all().select_related(
        'resolution', 'issueType', 'assignee__profile', 'reporter__profile', 'priority', 'column'
    )

    projectsList = request.GET.get('projects', [])
    issueTypesList = request.GET.get('issueTypes', [])
    resolutionsList = request.GET.get('resolutions', [])
    priorityList = request.GET.get('priorities', [])
    componentList = request.GET.get('component', [])

    if len(projectsList) > 0:
        projectsList = projectsList.split(',')
        allTickets = allTickets.filter(project__code__in=projectsList)

    if len(issueTypesList) > 0:
        issueTypesList = issueTypesList.split(',')
        allTickets = allTickets.filter(issueType__code__in=issueTypesList)

    if len(resolutionsList) > 0:
        resolutionsList = resolutionsList.split(',')
        allTickets = allTickets.filter(resolution__code__in=resolutionsList)

    if len(priorityList) > 0:
        priorityList = priorityList.split(',')
        allTickets = allTickets.filter(priority__code__in=priorityList)

    if len(componentList) > 0:
        componentList = componentList.split(',')
        allTickets = allTickets.filter(component__internalKey__in=componentList)

    # TODO: serializeTickets
    tickets = [
        {
            'id': t.id,
            'internalKey': t.internalKey,
            'summary': t.summary,
            'resolution': t.resolution.internalKey,
            'created': t.createdDttm.date(),
            'modified': t.modifiedDttm.date(),
            'link': t.getTicketUrl(),
            'issueType': {
                'internalKey': t.issueType.internalKey,
                'icon': t.issueType.icon,
            },
            'column': {
                'internalKey': t.column.internalKey,
                'colour': t.column.colour,
            },
            'priority': {
                'internalKey': t.priority.internalKey,
                'icon': t.priority.icon
            },
            'assignee': {
                'id': t.assignee.pk,
                'firstName': t.assignee.first_name,
                'lastName': t.assignee.last_name,
                'icon': t.assignee.profile.profilePicture.url
            } if t.assignee is not None else None,
            'reporter': {
                'id': t.reporter.pk,
                'firstName': t.reporter.first_name,
                'lastName': t.reporter.last_name,
                'icon': t.reporter.profile.profilePicture.url
            } if t.reporter is not None else None,
        }
        for t in allTickets
    ]

    context = {
        'tickets': tickets,
    }
    return render(request, 'jira/issuesListView.html', context)


def issuesDetailView(request):
    return render(request, 'jira/issuesDetailView.html')


def profileAndSettings(request):
    pass


@login_required
def newTicketObject(request):
    thisProject = Project.objects.filter(id=request.POST['project']).first()
    issueType = Component.objects.get(componentGroup__code='TICKET_ISSUE_TYPE', id=request.POST["ticketIssueType"])
    priority = Component.objects.get(componentGroup__code='TICKET_PRIORITY', id=request.POST["ticketPriority"])
    newTicketNumber = thisProject.projectTickets.count() + 1
    thisBoard = Board.objects.get(id=request.POST['board'])
    assignee = User.objects.get(id=request.POST['assignee'])

    newTicket = Ticket()
    newTicket.internalKey = thisProject.code + "-" + str(newTicketNumber)
    newTicket.summary = request.POST["summary"]
    newTicket.description = request.POST["description"]
    newTicket.resolution = Component.objects.get(componentGroup__code='TICKET_RESOLUTIONS', code="UNRESOLVED")
    newTicket.project = thisProject
    newTicket.assignee = assignee
    newTicket.reporter = request.user

    if request.POST['storyPoints']:
        newTicket.storyPoints = request.POST["storyPoints"]

    newTicket.issueType = issueType
    newTicket.priority = priority
    newTicket.board = thisBoard
    newTicket.column = Column.objects.get(board=thisBoard, internalKey='TO DO')
    newTicket.orderNo = newTicketNumber
    newTicket.save()

    return redirect(request.META.get('HTTP_REFERER'))
