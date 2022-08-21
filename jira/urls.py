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
        'api/v1/kanbanBoardActiveEpicLessTicketsApiEventVersion1Component/<int:boardId>',
        KanbanBoardActiveEpicLessTicketsApiEventVersion1Component.as_view(),
        name='kanbanBoardActiveEpicLessTicketsApiEventVersion1Component'
    ),
    path(
        'api/v1/kanbanBoardInActiveEpicLessTicketsApiEventVersion1Component/<int:boardId>',
        KanbanBoardInActiveEpicLessTicketsApiEventVersion1Component.as_view(),
        name='kanbanBoardInActiveEpicLessTicketsApiEventVersion1Component'
    ),
    path(
        'api/v1/scrumBoardSprintTicketsApiEventVersion1Component/<int:boardId>',
        ScrumBoardSprintTicketsApiEventVersion1Component.as_view(),
        name='scrumBoardSprintTicketsApiEventVersion1Component'
    )
    , path(
        'api/v1/sprintObjectApiEventVersion1Component/<int:boardId>',
        SprintObjectApiEventVersion1Component.as_view(),
        name='sprintObjectApiEventVersion1Component'
    ),
    path(
        'api/v1/kanbanBoardDetailsAndItemsApiEventVersion1Component/<int:boardId>',
        KanbanBoardDetailsAndItemsApiEventVersion1Component.as_view(),
        name='kanbanBoardDetailsAndItemsApiEventVersion1Component'
    ),
    path(
        'api/v1/kanbanBoardTicketColumnUpdateApiEventVersion1Component',
        KanbanBoardTicketColumnUpdateApiEventVersion1Component.as_view(),
        name='kanbanBoardTicketColumnUpdateApiEventVersion1Component'
    ),
    path(
        'api/v1/kanbanBoardBacklogInActiveTicketsApiEventVersion1Component/<int:boardId>',
        KanbanBoardBacklogInActiveTicketsApiEventVersion1Component.as_view(),
        name='kanbanBoardBacklogInActiveTicketsApiEventVersion1Component'
    ),
    path(
        'api/v1/kanbanBoardBacklogActiveTicketsApiEventVersion1Component/<int:boardId>',
        KanbanBoardBacklogActiveTicketsApiEventVersion1Component.as_view(),
        name='kanbanBoardBacklogActiveTicketsApiEventVersion1Component'
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
