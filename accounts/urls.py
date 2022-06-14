from django.urls import path

from accounts import views

app_name = "accounts"

urlpatterns = [
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout, name='logout'),
    path('activate-account/<uidb64>/<token>', views.activateAccount, name='activate-account'),
    # path('password-forgotten/', views.passwordForgotten, name='password-forgotten'),
    # path('password-change/<uidb64>/<token>', views.passwordChange, name='password-change'),
    # path('passwordRequest/', views.passwordRequest, name='password-request'),
    # path('passwordChange/<uidb64>/<token>', views.passwordChange, name='password-change'),
]
