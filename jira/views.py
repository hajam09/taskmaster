# Create your views here.
from django.http import Http404
from django.shortcuts import render

from accounts.models import Profile
from jira.models import Board, Project


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


def boards(request):
    """
       TODO: Allow user to copy board on template and make changes before creating new board.
    """
    privateAdminBoards = Board.object.filter(isPrivate=True, admins__in=[request.user]).prefetch_related('projects',
                                                                                                          'admins__profile')
    privateMemberBoards = Board.object.filter(isPrivate=True, members__in=[request.user]).prefetch_related('projects',
                                                                                                            'admins__profile')
    nonPrivateBoards = Board.object.filter(isPrivate=False).prefetch_related('projects', 'admins__profile')
    profiles = Profile.object.all().select_related('user')
    allProjects = (Project.object.filter(isPrivate=True, members__in=[request.user]) | Project.object.filter(
        isPrivate=False)).distinct()

    allBoards = (privateAdminBoards | privateMemberBoards | nonPrivateBoards).distinct()
    context = {
        'projects': allProjects,
        'boards': allBoards,
        'profiles': profiles
    }
    return render(request, 'jira/boards.html', context)


def board(request, url):
    try:
        thisBoard = Board.objects.get(url=url)
    except Board.DoesNotExist:
        raise Http404

    if thisBoard.isPrivate:
        if not request.user in thisBoard.members.all() or not request.user in thisBoard.admins.all():
            # TODO: Show access denied page.
            pass

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


def projects(request):
    pass


def project(request, url):
    pass


def projectSettings(request, url):
    pass


def createProject(request):
    pass


def profileAndSettings(request):
    pass


def projectIssues(request, projectId):
    pass


def projectBacklog(request, projectId):
    pass
