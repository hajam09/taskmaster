# Create your views here.
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404
from django.shortcuts import render

from accounts.models import Profile
from jira.models import Board, Project, Column


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
       TODO: Add Datatables to the table.
       TODO: Inform that in some places the project will appear to other users.
    """
    allBoards = Board.object.all().prefetch_related('projects', 'admins', 'members')
    allProfiles = Profile.object.all().select_related('user')
    allProjects = Project.object.filter(Q(isPrivate=True, members__in=[request.user]) | Q(isPrivate=False))

    if request.method == "POST":
        boardAdmins = [i.user for i in allProfiles if str(i.user.pk) in request.POST.getlist('board-admins')]
        boardMembers = [i.user for i in allProfiles if str(i.user.pk) in request.POST.getlist('board-members')]
        boardProjects = [i for i in allProjects if str(i.pk) in request.POST.getlist('board-projects')]

        # TODO: If board already exists with the name, then return a message to user.
        newBoard = Board.object.create(
            internalKey=request.POST['board-name'],
            isPrivate=request.POST['board-visibility'] == 'visibility-members'
        )

        # mandatory columns for a board
        Column.object.bulk_create(
            [
                Column(board=newBoard, internalKey='BACKLOG'),
                Column(board=newBoard, internalKey='TO DO'),
                Column(board=newBoard, internalKey='IN PROGRESS'),
                Column(board=newBoard, internalKey='DONE')
            ]
        )

        newBoard.projects.add(*boardProjects)
        newBoard.members.add(*boardMembers)
        newBoard.admins.add(*boardAdmins)

        allBoards = Board.object.all().prefetch_related('projects', 'admins', 'members')

    context = {
        'projects': allProjects,
        'profiles': allProfiles,
        'boards': allBoards,
    }
    return render(request, 'jira/boards.html', context)


def board(request, url):
    try:
        thisBoard = Board.objects.get(url=url)
    except Board.DoesNotExist:
        raise Http404

    if not thisBoard.hasAccessPermission(request.user):
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
