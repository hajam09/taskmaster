from django.urls import path

from core.api import (
    BoardColumnAndStatusApiVersion1,
    TicketColumStatusApiVersion1,
    ScrumBoardBacklogTicketUpdateApiVersion1,
    StartSprintEventApiVersion1,
    CompleteSprintEventApiVersion1,
    TicketOrderNoUpdateApiV1,
    TicketTypeListApiVersion1,
    TicketPriorityListApiVersion1,
    ColumnStatusListApiVersion1,
    ResolutionListApiVersion1,
    ProjectListApiVersion1,
    UserListApiVersion1,
    ProjectStatusListApiVersion1,
    LabelListApiVersion1,
    LabelLiveSearchApiVersion1,
    UserLiveSearchApiVersion1,
    TicketApiVersion1,
    TicketLiveSearchApiVersion1,
    TicketCommentListCreateView,
    TicketCommentDetailView,
)
from core.views import (
    loginView,
    registerView,
    logoutView,
    activateAccountView,
    forgotPasswordView,
    profileView,
    setPasswordView,
    teamsView,
    teamView,
    projectsView,
    projectView,
    boardsView,
    boardView,
    backlogView,
    boardSettingsView,
    labelsView,
    labelView,
    ticketsView,
    ticketView,
    newTicketView,
)

app_name = 'core'

urlpatterns = [
    path('login/', loginView, name='login-view'),
    path('register/', registerView, name='register-view'),
    path('logout/', logoutView, name='logout-view'),
    path('activate-account/<encodedId>/<token>', activateAccountView, name='activate-account-view'),
    path('forgot-password/', forgotPasswordView, name='forgot-password-view'),
    path('set-password/<encodedId>/<token>', setPasswordView, name='set-password-view'),
    path('profile/', profileView, name='profile-view'),
    path('teams/', teamsView, name='teams-view'),
    path('teams/<slug:url>/', teamView, name='team-view'),
    path('projects/', projectsView, name='projects-view'),
    path('projects/<slug:url>/', projectView, name='project-view'),
    path('boards/', boardsView, name='boards-view'),
    path('boards/<slug:url>/', boardView, name='board-view'),
    path('boards/<slug:url>/backlog', backlogView, name='board-backlog-view'),
    path('boards/<slug:url>/settings', boardSettingsView, name='board-settings-view'),
    path('labels/', labelsView, name='labels-view'),
    path('labels/<slug:url>/', labelView, name='label-view'),
    path('tickets/', ticketsView, name='tickets-view'),
    path('tickets/new/', newTicketView, name='new-ticket-view'),
    path('tickets/<slug:url>/', ticketView, name='ticket-view'),
]

urlpatterns += [
    path(
        'api/v1/boardColumnAndStatusApiVersion1/',
        BoardColumnAndStatusApiVersion1.as_view(),
        name='boardColumnAndStatusApiVersion1'
    ),
    path(
        'api/v1/ticketColumStatusApiVersion1/',
        TicketColumStatusApiVersion1.as_view(),
        name='ticketColumStatusApiVersion1'
    ),
    path(
        'api/v1/scrumBoardBacklogTicketUpdateApiVersion1/',
        ScrumBoardBacklogTicketUpdateApiVersion1.as_view(),
        name='scrumBoardBacklogTicketUpdateApiVersion1'
    ),
    path(
        'api/v1/startSprintEventApiVersion1/',
        StartSprintEventApiVersion1.as_view(),
        name='startSprintEventApiVersion1'
    ),
    path(
        'api/v1/completeSprintEventApiVersion1/',
        CompleteSprintEventApiVersion1.as_view(),
        name='completeSprintEventApiVersion1'
    ),
    path(
        'api/v1/ticketOrderNoUpdateApiV1/',
        TicketOrderNoUpdateApiV1.as_view(),
        name='ticketOrderNoUpdateApiV1'
    ),
    path(
        'api/v1/ticketTypeListApiVersion1/',
        TicketTypeListApiVersion1.as_view(),
        name='ticketTypeListApiVersion1'
    ),
    path(
        'api/v1/ticketPriorityListApiVersion1/',
        TicketPriorityListApiVersion1.as_view(),
        name='ticketPriorityListApiVersion1'
    ),
    path(
        'api/v1/columnStatusListApiVersion1/',
        ColumnStatusListApiVersion1.as_view(),
        name='columnStatusListApiVersion1'
    ),
    path(
        'api/v1/resolutionListApiVersion1/',
        ResolutionListApiVersion1.as_view(),
        name='resolutionListApiVersion1'
    ),
    path(
        'api/v1/projectListApiVersion1/',
        ProjectListApiVersion1.as_view(),
        name='projectListApiVersion1'
    ),
    path(
        'api/v1/userListApiVersion1/',
        UserListApiVersion1.as_view(),
        name='userListApiVersion1'
    ),
    path(
        'api/v1/projectStatusListApiVersion1/',
        ProjectStatusListApiVersion1.as_view(),
        name='projectStatusListApiVersion1'
    ),
    path(
        'api/v1/labelListApiVersion1/',
        LabelListApiVersion1.as_view(),
        name='labelListApiVersion1'
    ),
    path(
        'api/v1/ticketLiveSearchApiVersion1/',
        TicketLiveSearchApiVersion1.as_view(),
        name='ticketLiveSearchApiVersion1'
    ),
    path(
        'api/v1/userLiveSearchApiVersion1/',
        UserLiveSearchApiVersion1.as_view(),
        name='userLiveSearchApiVersion1'
    ),
    path(
        'api/v1/labelLiveSearchApiVersion1/',
        LabelLiveSearchApiVersion1.as_view(),
        name='labelLiveSearchApiVersion1'
    ),
    path(
        'api/v1/ticketApiVersion1/',
        TicketApiVersion1.as_view(),
        name='ticketApiVersion1'
    )
]


urlpatterns += [
    path(
        'tickets/<int:ticket_id>/comments/',
        TicketCommentListCreateView.as_view(),
        name='ticket-comments'
    ),

    path(
        'tickets/<int:ticket_id>/comments/<int:pk>/',
        TicketCommentDetailView.as_view(),
        name='ticket-comment-detail'
    ),
]
