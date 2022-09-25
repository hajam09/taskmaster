from django.urls import reverse

from jira.models import Board


class Icon:

    def __init__(self, name, clazz, size):
        self.name = name
        self.clazz = clazz
        self.size = size


def getIcon(icon):
    if icon is None:
        return None
    return '<i style="font-size:{}px" class="{}">{}</i>'.format(icon.size, icon.clazz, icon.name)


def linkItem(name, url, icon=None, subLinks=None):
    return {'name': name, 'url': url, 'icon': getIcon(icon), 'subLinks': subLinks}


def panelItems(boardUrl):
    thisBoard = Board.objects.filter(url=boardUrl).first()
    boardsInProject = Board.objects.filter(
        projects__in=thisBoard.projects.all().values_list('id', flat=True)
    ).distinct()

    links = [
        linkItem('Settings', '', Icon('&#xf085', 'fa', '24'), [
            linkItem('General', reverse('jira:board-settings', kwargs={'url': boardUrl})),
            linkItem('Columns', reverse('jira:board-settings-columns', kwargs={'url': boardUrl})),
        ]),
        linkItem('Board', reverse('jira:board-page', kwargs={'url': boardUrl}), Icon('&#xf24d', 'far', '24')),
        linkItem('Boards in this project', '', Icon('&#xf24d', 'far', '24'), [
            linkItem(otherBoard.internalKey, reverse('jira:board-page', kwargs={'url': otherBoard.url}))
            for otherBoard in boardsInProject
        ]),
        linkItem('Backlog', reverse('jira:board-backlog', kwargs={'url': boardUrl}), Icon('', 'fas fa-tasks', '24')),
    ]
    return links
