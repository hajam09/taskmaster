from django.urls import path

from ticket.api import (
    EpicIssueListCreateView,
    LabelLiveSearchApiVersion1,
    TicketApiVersion1,
    TicketCommentDetailView,
    TicketCommentListCreateView,
    TicketLiveSearchApiVersion1,
    TicketOrderNoUpdateApiV1,
    TicketSubTaskListCreateView,
    UserLiveSearchApiVersion1,
    TicketLinkedIssueListCreateView,
)
from ticket.views import ticketView

app_name = 'ticket'

urlpatterns = [
    path('tickets/<slug:url>/', ticketView, name='ticket-view'),
    path(
        'api/v1/ticketLiveSearchApiVersion1/',
        TicketLiveSearchApiVersion1.as_view(),
        name='ticketLiveSearchApiVersion1',
    ),
    path(
        'api/v1/userLiveSearchApiVersion1/',
        UserLiveSearchApiVersion1.as_view(),
        name='userLiveSearchApiVersion1',
    ),
    path(
        'api/v1/labelLiveSearchApiVersion1/',
        LabelLiveSearchApiVersion1.as_view(),
        name='labelLiveSearchApiVersion1',
    ),
    path(
        'api/v1/ticketApiVersion1/',
        TicketApiVersion1.as_view(),
        name='ticketApiVersion1',
    ),
    path(
        'api/v1/ticketOrderNoUpdateApiV1/',
        TicketOrderNoUpdateApiV1.as_view(),
        name='ticketOrderNoUpdateApiV1',
    ),
    path(
        'tickets/<slug:ticketIdOrUrl>/epic-issues/',
        EpicIssueListCreateView.as_view(),
        name='ticket-epic-issues',
    ),
    path(
        'tickets/<slug:ticketIdOrUrl>/subtasks/',
        TicketSubTaskListCreateView.as_view(),
        name='ticket-subtasks',
    ),
    path(
        'tickets/<slug:ticketIdOrUrl>/linked-issues/',
        TicketLinkedIssueListCreateView.as_view(),
        name='ticket-linked-issues',
    ),

    path(
        'tickets/<int:ticketId>/comments/',
        TicketCommentListCreateView.as_view(),
        name='ticket-comments',
    ),
    path(
        'tickets/<int:ticketId>/comments/<int:pk>/',
        TicketCommentDetailView.as_view(),
        name='ticket-comment-detail',
    ),
]
