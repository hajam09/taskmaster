from django.urls import path

from jira import views
from jira.api import *

app_name = "jira"

urlpatterns = [
    # path('', views.mainPage, name='main-page'),
    path('dashboard/', views.dashboard, name='dashboard-view'),
    path('issuesListView/', views.issuesListView, name='issuesListView'),
    path('ticket/<slug:internalKey>/', views.ticketDetailView, name='ticket-detail-view'),
    path('projects/', views.projects, name='projects-page'),
    path('projects/<slug:url>/settings', views.projectSettings, name='project-settings'),
    path('boards/', views.boards, name='boards-page'),
    path('boards/<slug:url>/', views.board, name='board-page'),
    path('boards/<slug:url>/settings/', views.boardSettings, name='board-settings'),
    path('boards/<slug:url>/settings/columns', views.boardSettingsColumns, name='board-settings-columns'),
    path('boards/<slug:url>/backlog/', views.backlog, name='board-backlog'),
    path('teams/', views.teams, name='teams-page'),
    path('teams/<slug:url>/', views.team, name='team-page'),
    path('new-ticket-object', views.newTicketObject, name='new-ticket-object'),
]

# api
urlpatterns += [
    path(
        'api/v1/boardSettingsViewGeneralDetailsApiEventVersion1Component/<slug:url>',
        BoardSettingsViewGeneralDetailsApiEventVersion1Component.as_view(),
        name='boardSettingsViewGeneralDetailsApiEventVersion1Component'
    ),
    path(
        'api/v1/boardSettingsViewBoardColumnsApiEventVersion1Component/<slug:url>',
        BoardSettingsViewBoardColumnsApiEventVersion1Component.as_view(),
        name='boardSettingsViewBoardColumnsApiEventVersion1Component'
    ),
    path(
        'api/v1/boardColumnsBulkOrderChangeApiEventVersion1Component/<slug:url>',
        BoardColumnsBulkOrderChangeApiEventVersion1Component.as_view(),
        name='boardColumnsBulkOrderChangeApiEventVersion1Component'
    ),
    path(
        'api/v1/boardSettingsViewBoardLabelsApiEventVersion1Component/<slug:url>',
        BoardSettingsViewBoardLabelsApiEventVersion1Component.as_view(),
        name='boardSettingsViewBoardLabelsApiEventVersion1Component'
    ),
    path(
        'api/v1/teamsViewApiEventVersion1Component/<slug:teamId>',
        TeamsViewApiEventVersion1Component.as_view(),
        name='teamsViewApiEventVersion1Component'
    ),
    path(
        'api/v1/teamsObjectApiEventVersion1Component/<slug:teamId>',
        TeamsObjectApiEventVersion1Component.as_view(),
        name='teamsObjectApiEventVersion1Component'
    ),
    path(
        'api/v1/subTaskTicketObjectForTicketApiEventVersion1Component',
        SubTaskTicketObjectForTicketApiEventVersion1Component.as_view(),
        name='subTaskTicketObjectForTicketApiEventVersion1Component'
    ),
    path(
        'api/v1/ticketAttachmentsApiEventVersion1Component/<int:ticketId>',
        TicketAttachmentsApiEventVersion1Component.as_view(),
        name='ticketAttachmentsApiEventVersion1Component'
    ),
    path(
        'api/v1/ticketsForEpicTicketApiEventVersion1Component/<int:ticketId>',
        TicketsForEpicTicketApiEventVersion1Component.as_view(),
        name='ticketsForEpicTicketApiEventVersion1Component'
    ),
    path(
        'api/v1/ticketCommentsApiEventVersion1Component/<int:ticketId>',
        TicketCommentsApiEventVersion1Component.as_view(),
        name='ticketCommentsApiEventVersion1Component'
    ),
    path(
        'api/v1/ticketObjectForEpicTicketApiEventVersion1Component/',
        TicketObjectForEpicTicketApiEventVersion1Component.as_view(),
        name='ticketObjectForEpicTicketApiEventVersion1Component'
    ),
    path(
        'api/v1/ticketCommentObjectApiEventVersion1Component/',
        TicketCommentObjectApiEventVersion1Component.as_view(),
        name='ticketCommentObjectApiEventVersion1Component'
    ),
    path(
        'api/v1/ticketBulkOrderChangeApiEventVersion1Component/',
        TicketBulkOrderChangeApiEventVersion1Component.as_view(),
        name='ticketBulkOrderChangeApiEventVersion1Component'
    ),
    path(
        'api/v1/subTaskTicketsForTicketApiEventVersion1Component/<int:ticketId>',
        SubTaskTicketsForTicketApiEventVersion1Component.as_view(),
        name='subTaskTicketsForTicketApiEventVersion1Component'
    ),
    path(
        'api/v1/ticketObjectDetailApiEventVersion1Component/<int:ticketId>',
        TicketObjectDetailApiEventVersion1Component.as_view(),
        name='ticketObjectDetailApiEventVersion1Component'
    ),
    path(
        'api/v1/sprintObjectApiEventVersion1Component/<int:boardId>',
        SprintObjectApiEventVersion1Component.as_view(),
        name='sprintObjectApiEventVersion1Component'
    ),
    path(
        'api/v1/agileBoardColumnOperationApiEventVersion1Component/<int:boardId>',
        AgileBoardColumnOperationApiEventVersion1Component.as_view(),
        name='agileBoardColumnOperationApiEventVersion1Component'
    ),
    path(
        'api/v1/agileBoardDetailsApiEventVersion1Component/<int:boardId>',
        AgileBoardDetailsApiEventVersion1Component.as_view(),
        name='agileBoardDetailsApiEventVersion1Component'
    ),
    path(
        'api/v2/agileBoardDetailsApiEventVersion2Component/<int:boardId>',
        AgileBoardDetailsApiEventVersion2Component.as_view(),
        name='agileBoardDetailsApiEventVersion2Component'
    ),
    path(
        'api/v1/agileBoardTicketColumnUpdateApiEventVersion1Component',
        AgileBoardTicketColumnUpdateApiEventVersion1Component.as_view(),
        name='agileBoardTicketColumnUpdateApiEventVersion1Component'
    ),
    path(
        'api/v2/agileBoardTicketColumnUpdateApiEventVersion2Component',
        AgileBoardTicketColumnUpdateApiEventVersion2Component.as_view(),
        name='agileBoardTicketColumnUpdateApiEventVersion2Component'
    ),
    path(
        'api/v1/backlogDetailsEpicLessTicketsApiEventVersion1Component/<int:boardId>',
        BacklogDetailsEpicLessTicketsApiEventVersion1Component.as_view(),
        name='backlogDetailsEpicLessTicketsApiEventVersion1Component'
    ),
    path(
        'api/v1/backlogDetailsApiEventVersion1Component/<int:boardId>',
        BacklogDetailsApiEventVersion1Component.as_view(),
        name='backlogDetailsApiEventVersion1Component'
    ),
    path(
        'api/v2/backlogDetailsApiEventVersion2Component/<int:boardId>',
        BacklogDetailsApiEventVersion2Component.as_view(),
        name='backlogDetailsApiEventVersion2Component'
    ),
    path(
        'api/v1/epicDetailsForBoardApiEventVersion1Component/<int:boardId>',
        EpicDetailsForBoardApiEventVersion1Component.as_view(),
        name='epicDetailsForBoardApiEventVersion1Component'
    ),
    path(
        'api/v1/teamChatMessagesApiEventVersion1Component/<slug:url>',
        TeamChatMessagesApiEventVersion1Component.as_view(),
        name='teamChatMessagesApiEventVersion1Component'
    ),
    path(
        'api/v1/ticketObjectBulkCreateApiEventVersion1Component',
        TicketObjectBulkCreateApiEventVersion1Component.as_view(),
        name='ticketObjectBulkCreateApiEventVersion1Component'
    ),
]
