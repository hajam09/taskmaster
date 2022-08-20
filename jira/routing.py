from django.urls import path

from jira import consumers

webSocketUrlPatterns = [
    path('jira/teams/<slug:url>/', consumers.ChatConsumer.as_asgi()),
]
