from django.contrib import messages
from django.urls import resolve, reverse

from core.forms import TicketForm

allowed_urls = [
    'teams-view',
    'team-view',
    'projects-view',
    'project-view',
    'boards-view',
    'board-view',
    'board-backlog-view',
    'board-settings-view',
    'labels-view',
    'label-view',
    'tickets-view',
    'ticket-view',
]


def ticketForm(request):
    if not request.user.is_authenticated:
        return {}

    match = resolve(request.path)
    if match.url_name not in allowed_urls:
        return {}

    return {'ticketForm': TicketForm(request)}
