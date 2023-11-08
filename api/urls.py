# from django.urls import path
#
# from api.views import TeamModelViewSetApiVersion1, BoardModelViewSetApiVersion1, ProjectModelViewSetApiVersion1, \
#     TeamViewSetApiVersion1, TicketModelViewSetApiVersion1, DashboardViewSetApiVersion1
#
# urlpatterns = [
#
#     path('v1/teams/<str:url>/', TeamModelViewSetApiVersion1.as_view({'get': 'retrieve'}), name='v1-teams-detail'),
#     path('v1/teams/', TeamModelViewSetApiVersion1.as_view({'get': 'list', 'post': 'create'}), name='v1-teams-list'),
#
#     path('v1/boards/<str:url>/', BoardModelViewSetApiVersion1.as_view({'get': 'retrieve'}), name='v1-boards-detail'),
#     path('v1/boards/', BoardModelViewSetApiVersion1.as_view({'get': 'list'}), name='v1-boards-list'),
#
#     path('v1/projects/<str:url>/', ProjectModelViewSetApiVersion1.as_view({'get': 'retrieve'}),
#          name='v1-projects-detail'),
#     path('v1/projects/', ProjectModelViewSetApiVersion1.as_view({'get': 'list'}), name='v1-projects-list'),
#
#     path('v1/tickets/<str:internalKey>/', TicketModelViewSetApiVersion1.as_view({'get': 'retrieve'}),
#          name='v1-tickets-detail'),
#
#     path('v1/dashboard/', DashboardViewSetApiVersion1.as_view({'get': 'list'}), name='v1-dashboard'),
#     path('v1/team-view/<str:url>/', TeamViewSetApiVersion1.as_view({'get': 'retrieve'}), name='v1-teams-instance-view'),
#
# ]
