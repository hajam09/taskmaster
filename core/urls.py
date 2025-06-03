from django.urls import path

from core.api import (
    BoardColumnAndStatusApiVersion1,
    TicketColumStatusApiVersion1,
    ScrumBoardBacklogTicketUpdateApiVersion1,
    ScrumBoardBacklogSprintUpdateApiVersion1,
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
    ticketView
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
    path('ticket/<slug:url>/', ticketView, name='ticket-view'),
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
    ),path(
        'api/v1/scrumBoardBacklogSprintUpdateApiVersion1/',
        ScrumBoardBacklogSprintUpdateApiVersion1.as_view(),
        name='scrumBoardBacklogSprintUpdateApiVersion1'
    )
]
