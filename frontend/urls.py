from django.urls import path

from frontend.views import index

urlpatterns = [
    path('', index),
    path('teams/<slug:url>/', index),
    path('teams/', index),

    path('boards/', index),
    path('projects/', index),
]
