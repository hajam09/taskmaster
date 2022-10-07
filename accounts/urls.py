from django.urls import path

from accounts import views
from accounts.api import *

app_name = "accounts"

urlpatterns = [
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout, name='logout'),
    path('activate-account/<uidb64>/<token>', views.activateAccount, name='activate-account'),
    path('password-forgotten/', views.passwordForgotten, name='password-forgotten'),
    path('password-reset/<uidb64>/<token>', views.passwordReset, name='password-reset'),
    path('account-settings', views.accountSettings, name='account-settings'),
]

# api
urlpatterns += [
    path(
        'api/v1/accountSettingsSecurityPasswordUpdateApiEventVersion1Component/',
        AccountSettingsSecurityPasswordUpdateApiEventVersion1Component.as_view(),
        name='accountSettingsSecurityPasswordUpdateApiEventVersion1Component'
    ),
    path(
        'api/v1/userDetailsApiEventVersion1Component/',
        UserDetailsApiEventVersion1Component.as_view(),
        name='userDetailsApiEventVersion1Component'
    ),
    path(
        'api/v1/userProfilePictureApiEventVersion1Component/',
        UserProfilePictureApiEventVersion1Component.as_view(),
        name='userProfilePictureApiEventVersion1Component'
    ),
]
