import operator
from functools import reduce

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.db.models import Q
from django.http import Http404
from django.shortcuts import render, redirect

from accounts.models import Profile, Component, Team
from jira.forms import ProjectSettingsForm, TeamForm
from jira.models import Board, Project, Column, Ticket, TicketAttachment, Label, ColumnStatus, Sprint, ProjectComponent
from taskmaster.operations import emailOperations, generalOperations

generalOperations.setCaches()


@login_required
def index(request):
    return render(request, "jira/index.html")


def dashboard(request):
    # 6 queries
    projectComponents = Component.objects.filter(componentGroup__code='PROJECT_COMPONENTS').prefetch_related(
        'ticketComponents__issueType', 'ticketComponents__priority'
    )
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


@login_required
def teams(request):
    # 6 queries
    allTeams = Team.objects.all().prefetch_related('admins', 'members')

    if request.method == "POST":
        form = TeamForm(request, request.POST)
        if len(form.errors) == 2:
            form.save()
            return redirect('jira:teams-page')

        del form.errors['admins']
        del form.errors['members']

    else:
        form = TeamForm(request)

    context = {
        'teams': allTeams,
        'form': form,
    }
    return render(request, "jira/teams.html", context)


@login_required
def team(request, url):
    # 10 queries
    """
    TODO: Group messages by each day and display the date if message is sent on a new date.
    """
    try:
        thisTeam = Team.objects.get(url=url)
    except Team.DoesNotExist:
        raise Http404

    if not thisTeam.hasAccessPermission(request.user):
        raise PermissionDenied()

    if request.method == "POST":
        teamAdmins = request.POST.getlist('team-admins')
        teamMembers = request.POST.getlist('team-members')
        thisTeam.admins.add(*teamAdmins)
        thisTeam.members.add(*teamMembers)

        for user in set(thisTeam.admins.filter(id__in=teamAdmins) | thisTeam.members.filter(id__in=teamMembers)):
            emailOperations.sendEmailToNotifyUserAddedToTeam(request, user)

        return redirect('jira:team-page', url=url)

    memberIds = thisTeam.members.values_list('id', flat=True)
    adminIds = thisTeam.admins.values_list('id', flat=True)
    uniqueAssociateIds = set(memberIds | adminIds)

    allProfiles = Profile.objects.all().select_related('user')
    excludedMembers = allProfiles.exclude(user__id__in=memberIds)
    excludedAdmins = allProfiles.exclude(user__id__in=adminIds)

    teamTickets = Ticket.objects.filter(
        Q(assignee_id__in=uniqueAssociateIds) | Q(reporter_id__in=uniqueAssociateIds)
    ).select_related('priority', 'issueType', 'assignee__profile').order_by('-modifiedDttm')[:5]

    uniqueAssociates = set(
        thisTeam.admins.prefetch_related('profile') | thisTeam.members.prefetch_related('profile')
    )

    context = {
        "team": thisTeam,
        "teamTickets": teamTickets,
        "members": excludedMembers,
        "admins": excludedAdmins,
        "associates": uniqueAssociates,
        "hasChatPermission": request.user in uniqueAssociates,
    }
    return render(request, "jira/team.html", context)


def ticketDetailView(request, internalKey):
    # 7 queries
    """
    TODO: remove unused css on the ticket css files
    TODO: Fix linked issue component.
    TODO: Allow users to change EPIC colour on the ticket page.
    TODO: Show link to the board where the ticket resides.
    """

    try:
        ticket = Ticket.objects.select_related(
            'project', 'issueType', 'priority', 'assignee__profile', 'columnStatus__board'
        ).prefetch_related('label', 'component').get(internalKey__iexact=internalKey)
    except Ticket.DoesNotExist:
        raise Http404

    if request.method == "POST":

        for key, value in request.POST.items():
            value = value or None

            if hasattr(ticket, f"{key}_id"):
                setattr(ticket, f"{key}_id", int(value))
            elif hasattr(ticket, f"{key}"):
                setattr(ticket, f"{key}", value)

        ticket.component.clear()
        ticket.component.add(*request.POST.getlist('components'))

        # Add and amend labels
        updatedLabels = request.POST.getlist('labels')
        existingLabels = list(Label.objects.filter(internalKey__in=updatedLabels).values_list('internalKey', flat=True))

        Label.objects.bulk_create(
            [
                Label(
                    internalKey=i,
                    code=i.upper(),
                )
                for i in updatedLabels if i not in existingLabels
            ]
        )

        ids = list(Label.objects.filter(internalKey__in=updatedLabels).values_list('id', flat=True))
        ticket.label.clear()
        ticket.label.add(*ids)
        #

        TicketAttachment.objects.bulk_create(
            TicketAttachment(
                ticket=ticket,
                uploadedBy=request.user,
                internalKey=attachment.name,
                attachment=attachment
            )
            for attachment in request.FILES.getlist('attachments')
        )
        ticket.save()
        return redirect('jira:ticket-detail-view', internalKey=internalKey)

    ticketDetails = {
        "id": ticket.id,
        "internalKey": ticket.internalKey,
        "summary": ticket.summary,
        "storyPoints": ticket.storyPoints if ticket.storyPoints is not None else '',
        "fixVersion": ticket.fixVersion or '',
        "description": ticket.description if ticket.description is not None else '',
        "issueType": ticket.issueType.serializeComponentVersion1(),
        "priority": ticket.priority.serializeComponentVersion1(),
        "assignee": generalOperations.serializeUserVersion2(ticket.assignee),
        "components": [component.serializeComponentVersion1() for component in ticket.component.all()],
        "labels": [label.serializeLabelVersion1() for label in ticket.label.all()]
    }

    projectComponents = Component.objects.filter(
        componentGroup__code='PROJECT_COMPONENTS', reference__exact=ticket.project.code
    )
    context = {
        'ticket': ticketDetails,
        'profiles': Profile.objects.all().select_related('user'),
        'projectComponents': projectComponents,
    }
    return render(request, "jira/ticketDetailViewPage.html", context)


@login_required
def boards(request):
    # 9 queries
    if request.method == "POST":
        try:
            newBoard = Board.objects.create(
                internalKey=request.POST['boardName'],
                type=request.POST['boardType'],
                isPrivate=request.POST['boardVisibility'] == 'visibility-members'
            )

            c1 = Column(board=newBoard, internalKey='BACKLOG', category=Column.Category.TODO, colour='#42526E', orderNo=1)
            c2 = Column(board=newBoard, internalKey='TO DO', category=Column.Category.TODO, colour='#42526E', orderNo=2)
            c3 = Column(board=newBoard, internalKey='IN PROGRESS', category=Column.Category.IN_PROGRESS, colour='#0052CC', orderNo=3)
            c4 = Column(board=newBoard, internalKey='DONE', category=Column.Category.DONE, colour='#00875A', orderNo=4)

            c1.save()
            c2.save()
            c3.save()
            c4.save()

            # mandatory ColumnStatus for a board
            ColumnStatus.objects.bulk_create(
                [
                    ColumnStatus(internalKey="OPEN", board=newBoard, column=c1, category=ColumnStatus.Category.TODO, colour=ColumnStatus.Colour.TODO),
                    ColumnStatus(internalKey="TO DO", board=newBoard, column=c2, category=ColumnStatus.Category.TODO, colour=ColumnStatus.Colour.TODO),
                    ColumnStatus(internalKey="IN PROGRESS", board=newBoard, column=c3, category=ColumnStatus.Category.IN_PROGRESS, colour=ColumnStatus.Colour.IN_PROGRESS),
                    ColumnStatus(internalKey="DONE", board=newBoard, column=c4, setResolution=True, category=ColumnStatus.Category.DONE, colour=ColumnStatus.Colour.DONE)
                ]
            )

            if request.POST['boardType'] == Board.Types.SCRUM:
                Sprint.objects.create(
                    board=newBoard,
                    internalKey=f'{newBoard.internalKey} Sprint {1}',
                    orderNo=1,
                )

            newBoard.projects.add(*request.POST.getlist('boardProjects'))
            newBoard.members.add(*request.POST.getlist('boardMembers'))
            newBoard.admins.add(*request.POST.getlist('boardAdmins'))
        except IntegrityError:
            messages.error(
                request,
                f'Board with name {request.POST["boardName"]} already exists.'
            )
        return redirect('jira:boards-page')

    context = {
        'boards': Board.objects.all().prefetch_related('projects', 'admins', 'members'),
        'profiles': Profile.objects.all().select_related('user'),
        'projects': Project.objects.all(),
    }

    return render(request, 'jira/boards.html', context)


@login_required
def boardSettings(request, url):
    try:
        thisBoard = Board.objects.prefetch_related('admins').get(url=url)
    except Board.DoesNotExist:
        raise Http404

    tab = request.GET.get('tab', 'general').lower()
    TEMPLATE = None

    context = {
        'board': thisBoard,
        'isAdmin': request.user in thisBoard.admins.all(),
    }

    if tab == "general":
        # 10 queries
        TEMPLATE = "boardSettings"
        context['projects'] = Project.objects.filter(Q(isPrivate=True, members__in=[request.user]) | Q(isPrivate=False)).distinct()
        context['profiles'] = Profile.objects.all().select_related('user')
    elif tab == "columns":
        # 6 queries
        TEMPLATE = "boardSettingsColumns"
    return render(request, 'jira/{}.html'.format(TEMPLATE), context)


@login_required
def board(request, url):
    # 5 queries
    try:
        thisBoard = Board.objects.get(url=url)
    except Board.DoesNotExist:
        raise Http404

    if not thisBoard.hasAccessPermission(request.user):
        raise PermissionDenied()

    context = {
        "board": thisBoard,
    }
    return render(request, 'jira/agileBoard.html', context)


def backlog(request, url):
    # 5 queries
    try:
        thisBoard = Board.objects.get(url=url)
    except Board.DoesNotExist:
        raise Http404

    if not thisBoard.hasAccessPermission(request.user):
        raise PermissionDenied()

    context = {
        "board": thisBoard,
    }
    return render(request, "jira/backlog.html", context)


@login_required
def projects(request):
    # 4 queries
    if request.method == "POST":
        try:
            newProject = Project()
            newProject.internalKey = request.POST['projectName']
            newProject.code = request.POST['projectCode'].upper()
            newProject.description = request.POST['projectDescription']
            newProject.lead = request.user
            newProject.startDate = request.POST['projectStart'] or None
            newProject.endDate = request.POST['projectDue'] or None
            newProject.status_id = next((i.id for i in cache.get('PROJECT_STATUS') if i.code == 'ON_GOING'))
            newProject.icon = request.FILES.get('projectIcon')
            newProject.isPrivate = request.POST['projectVisibility'] == 'visibility-members'

            newProject.save()
            newProject.members.add(*request.POST.getlist('projectMembers'))

        except IntegrityError:
            messages.error(
                request,
                f'Project with code {request.POST["projectCode"]} already exists.'
            )
        return redirect('jira:projects-page')

    allProjects = Project.objects.filter(
        Q(isPrivate=True, members__in=[request.user]) | Q(isPrivate=False)
    ).distinct().select_related('status', 'lead')

    context = {
        'projects': allProjects,
    }
    return render(request, 'jira/projects.html', context)


@login_required
def projectSettings(request, url):
    # 11 queries
    try:
        project = Project.objects.prefetch_related(
            'boardProjects__admins', 'boardProjects__members', 'boardProjects__projects'
        ).select_related('lead').get(url=url)
    except Project.DoesNotExist:
        raise Http404

    if request.method == "POST":
        form = ProjectSettingsForm(request, project, request.POST)
        form.save()
    else:
        form = ProjectSettingsForm(request, project)

    context = {
        'form': form,
        'project': project,
        'component': project.components.values_list('internalKey', flat=True)
    }
    return render(request, 'jira/projectSettings.html', context)


def projectComponents(request, url):
    try:
        project = Project.objects.get(url=url)
    except Project.DoesNotExist:
        raise Http404

    context = {
        'project': project
    }
    return render(request, 'jira/projectComponents.html', context)


def issuesListView(request):
    # 3 queries
    """
    TODO: Allow users to add dropdown manually.
    TODO: User pagination to improve query performance.
    """

    qFilterSet = []
    filterDict = {}
    for key, value in request.GET.items():
        """
        e.g.
        # (OR: ('project__internalKey__icontains', 'OneTutor'), ('project__internalKey__icontains', 'Dunder Mifflin'))
        
        querySet = (
                (Q(project__internalKey__icontains="OneTutor") | Q(project__internalKey__icontains="Dunder Mifflin"))
                &
                (Q(columnStatus__internalKey__icontains="In Progress"))
        )
        """

        qFilterSet.append(
            reduce(
                operator.or_, [Q(**{f'{key}__internalKey__icontains': v}) for v in value.split(',')]
            )
        )
        filterDict[f'{key}__internalKey__in'] = value.split(',')

    try:
        ticketQuerySet = Ticket.objects.filter(reduce(operator.and_, qFilterSet))
    except TypeError:
        # Ticket.objects.filter(**filterDict)
        ticketQuerySet = Ticket.objects.filter(**{})

    allTickets = ticketQuerySet.select_related(
        'resolution', 'issueType', 'assignee__profile', 'reporter__profile', 'priority', 'columnStatus'
    )

    tickets = [
        {
            'id': ticket.id,
            'internalKey': ticket.internalKey,
            'summary': ticket.summary,
            'created': ticket.createdDttm.date(),
            'modified': ticket.modifiedDttm.date(),
            'link': ticket.getTicketUrl(),
            'resolution': ticket.resolution.serializeComponentVersion1(),
            'issueType': ticket.issueType.serializeComponentVersion1(),
            'priority': ticket.priority.serializeComponentVersion1(),
            'status': ticket.columnStatus.serializeColumnStatusVersion1(),
            'assignee': generalOperations.serializeUserVersion1(ticket.assignee),
            'reporter': generalOperations.serializeUserVersion1(ticket.reporter),
        }
        for ticket in allTickets
    ]

    context = {
        'tickets': tickets,
    }
    return render(request, 'jira/issuesListView.html', context)


def yourWork(request):
    pass


def peopleAndTeamSearch(request):
    pass


@login_required
def newTicketObject(request):
    thisProject = Project.objects.filter(id=request.POST['project']).first()
    newTicketNumber = thisProject.projectTickets.count() + 1
    boardId = request.POST['board'] or None
    boardObject = Board.objects.get(id=boardId)
    columnName = "TO DO" if boardObject.type == Board.Types.KANBAN else "OPEN"
    columnStatus = ColumnStatus.objects.get(
        internalKey__icontains=columnName, board_id=boardId, category=Column.Category.TODO
    )
    assigneeId = request.POST['assignee'] if request.POST['assignee'] and request.POST['assignee'] != "0" else None

    newTicket = Ticket()
    newTicket.internalKey = thisProject.code + "-" + str(newTicketNumber)
    newTicket.summary = request.POST["summary"] or None
    newTicket.description = request.POST["description"] or None
    newTicket.resolution_id = next((i.id for i in cache.get('TICKET_RESOLUTIONS') if i.code == 'UNRESOLVED'))
    newTicket.project = thisProject
    newTicket.assignee_id = assigneeId
    newTicket.reporter = request.user
    newTicket.storyPoints = request.POST["storyPoints"] or None
    newTicket.issueType_id = request.POST["issueType"] or None
    newTicket.priority_id = request.POST["priority"] or None
    # newTicket.board_id = boardId
    # newTicket.column = Column.objects.get(board_id=boardId, internalKey='TO DO')
    newTicket.columnStatus = columnStatus
    newTicket.orderNo = newTicketNumber
    newTicket.save()

    messages.info(
        request,
        f"New issue created <a href='{newTicket.getTicketUrl()}'> {newTicket.internalKey} </a>"
    )
    return redirect(request.META.get('HTTP_REFERER'))
