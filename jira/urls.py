from django.urls import path

from jira import views

app_name = "jira"
urlpatterns = [
    # path('', views.mainPage, name='main-page'),
    # path('sprint-board/', views.sprintBoard, name='sprintBoard'),
    # path('back-log/', views.backLog, name='backLog'),
    # path('ticket/<slug:internalKey>/', views.ticketPage, name='ticket-page'),
    # path('projects/', views.projects, name='projects-page'),
    # path('project/<slug:url>/', views.project, name='project-page'),
    # path('project/<slug:url>/settings', views.projectSettings, name='project-settings'),
    path('boards/', views.boards, name='boards-page'),
    path('board/<slug:url>/', views.board, name='board-page'),
    # path('kanbanBoard/<slug:url>/', views.kanbanBoard, name='kanban-board-page'),
    # path('board/<slug:url>/settings/', views.boardSettings, name='board-settings'),
    # path('board/<slug:url>/backlog/', views.backlog, name='board-backlog'),
    # path('kanbanBoard/<slug:url>/backlog/', views.kanbanBoardBacklog, name='kanban-board-backlog'),
    # path('people/team/<slug:url>/', views.team, name='team-settings'),
]
