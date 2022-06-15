from django.urls import path

from accounts import views

app_name = "accounts"

urlpatterns = [
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout, name='logout'),
    path('activate-account/<uidb64>/<token>', views.activateAccount, name='activate-account'),
    path('password-forgotten/', views.passwordForgotten, name='password-forgotten'),
    path('password-reset/<uidb64>/<token>', views.passwordReset, name='password-reset'),
    path('manage-profile/profile-and-visibility', views.accountProfileAndVisibility, name='profile-and-visibility'),
    path('manage-profile/account-security', views.accountSecurity, name='account-security'),
]
