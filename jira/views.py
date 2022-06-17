# Create your views here.
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.db.models import Q
from django.http import Http404
from django.shortcuts import render

from accounts.models import Profile, Component
from jira.models import Board, Project, Column
from taskmaster.operations import databaseOperations


def index(request):
    pass


def dashboard(request):
    pass


def teams(request):
    pass


def team(request, url):
    pass


def peopleAndTeamSearch(request):
    pass


def profileView(request, url):
    pass


def ticketView(request, url):
    pass


@login_required
def boards(request):
    """
       TODO: Allow user to copy board on template and make changes before creating new board.
       TODO: Inform that in some places the project will appear to other users.
    """
    allBoards = Board.object.all().prefetch_related('projects', 'admins', 'members')
    allProfiles = Profile.object.all().select_related('user')
    allProjects = Project.object.filter(Q(isPrivate=True, members__in=[request.user]) | Q(isPrivate=False))

    if request.method == "POST":
        boardAdmins = [i.user for i in allProfiles if str(i.user.pk) in request.POST.getlist('board-admins')]
        boardMembers = [i.user for i in allProfiles if str(i.user.pk) in request.POST.getlist('board-members')]
        boardProjects = [i for i in allProjects if str(i.pk) in request.POST.getlist('board-projects')]

        try:
            newBoard = Board.object.create(
                internalKey=request.POST['board-name'],
                isPrivate=request.POST['board-visibility'] == 'visibility-members'
            )

            # mandatory columns for a board
            Column.object.bulk_create(
                [
                    Column(board=newBoard, internalKey='BACKLOG', orderNo=1),
                    Column(board=newBoard, internalKey='TO DO', orderNo=2),
                    Column(board=newBoard, internalKey='IN PROGRESS', orderNo=3),
                    Column(board=newBoard, internalKey='DONE', orderNo=4)
                ]
            )

            newBoard.projects.add(*boardProjects)
            newBoard.members.add(*boardMembers)
            newBoard.admins.add(*boardAdmins)

            allBoards = Board.object.all().prefetch_related('projects', 'admins', 'members')
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
        thisBoard = Board.object.prefetch_related('boardColumns', 'boardLabels').get(url=url)
    except Board.DoesNotExist:
        raise Http404

    allProjects = Project.object.filter(Q(isPrivate=True, members__in=[request.user]) | Q(isPrivate=False))
    allProfiles = Profile.object.all().select_related('user')

    context = {
        'board': thisBoard,
        'projects': allProjects,
        'profiles': allProfiles
    }
    return render(request, 'jira/boardSettings.html', context)


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
    return render(request, "jira2/board.html", context)


def kanbanBoardCreate(request):
    pass


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
    allProjects = Project.object.filter(projectQuery).select_related('status', 'lead')
    allProfiles = Profile.object.all().select_related('user')

    if request.method == "POST":
        newProject = Project()
        newProject.internalKey = request.POST['project-name']
        newProject.code = request.POST['project-code']
        newProject.description = request.POST['project-description']
        newProject.lead = request.user
        newProject.isPrivate = request.POST['project-visibility'] == 'visibility-members'
        newProject.status = Component.object.get(componentGroup__code='PROJECT_STATUS', code='ON_GOING')

        if request.FILES.get('project-icon'):
            newProject.icon = request.FILES.get('project-icon')

        if request.POST['project-start']:
            newProject.startDate = request.POST['project-start']

        if request.POST['project-due']:
            newProject.endDate = request.POST['project-due']

        newProject.save()
        newProject.members.add(*request.POST.getlist('project-users', []))

        allProjects = Project.object.filter(projectQuery).select_related('status', 'lead')

    context = {
        'projects': allProjects,
        'profiles': allProfiles
    }
    return render(request, 'jira/projects.html', context)


def project(request, url):
    pass


def projectSettings(request, url):
    try:
        thisProject = Project.object.get(url=url)
    except Project.DoesNotExist:
        raise Http404

    allProfiles = Profile.object.all().select_related('user')
    component = Component.object.filter(componentGroup__code='PROJECT_STATUS')

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


def profileAndSettings(request):
    pass


def projectIssues(request, projectId):
    pass


def projectBacklog(request, projectId):
    pass
