from django.urls import reverse

from jira.models import Board
from taskmaster.base.utils.navigationBar import linkItem, Icon


def panelItems(boardUrl):
    thisBoard = Board.objects.filter(url=boardUrl).first()
    boardsInProject = Board.objects.filter(
        projects__in=thisBoard.projects.all().values_list('id', flat=True)
    ).distinct()

    links = [
        linkItem('Settings', '', Icon('&#xf085', 'fa', '24'), [
            linkItem('General', f"{reverse('jira:board-settings', kwargs={'url': boardUrl})}?tab=general"),
            linkItem('Columns', f"{reverse('jira:board-settings', kwargs={'url': boardUrl})}?tab=columns"),
        ]),
        linkItem('Board', reverse('jira:board-page', kwargs={'url': boardUrl}), Icon('&#xf24d', 'far', '24')),
        linkItem('Boards in this project', '', Icon('&#xf24d', 'far', '24'), [
            linkItem(otherBoard.internalKey, reverse('jira:board-page', kwargs={'url': otherBoard.url}))
            for otherBoard in boardsInProject
        ]),
        linkItem('Backlog', reverse('jira:board-backlog', kwargs={'url': boardUrl}), Icon('', 'fas fa-tasks', '24')),
    ]
    return links
