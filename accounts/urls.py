from django.urls import path
from accounts import views

app_name = "accounts"

urlpatterns = [
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout, name='logout'),
    # path('passwordRequest/', views.passwordRequest, name='password-request'),
    # path('passwordChange/<uidb64>/<token>', views.passwordChange, name='password-change'),
]
