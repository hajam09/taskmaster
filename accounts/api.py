import json
import os
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.http import JsonResponse
from django.views import View
from django.db.models import Q
from accounts.models import Profile, Component
from taskmaster.operations import generalOperations


class AccountSettingsSecurityPasswordUpdateApiEventVersion1Component(View):

    def put(self, *args, **kwargs):
        put = json.loads(self.request.body)

        currentPassword = put.get('currentPassword')
        newPassword = put.get('newPassword')
        repeatNewPassword = put.get('repeatNewPassword')
        errors = []

        if not self.request.user.check_password(currentPassword):
            errors.append("Your current password does not match with the account\'s existing password.")

        if newPassword != repeatNewPassword:
            errors.append("Your new password and confirm password does not match.")

        if len(errors) != 0:
            response = {
                "success": False,
                "data": {
                    "errors": errors
                }
            }
            return JsonResponse(response, status=HTTPStatus.OK)

        self.request.user.set_password(newPassword)
        self.request.user.save()

        user = authenticate(username=self.request.user.username, password=newPassword)
        if user:
            login(self.request, user)

        response = {
            "success": True
        }
        return JsonResponse(response, status=HTTPStatus.OK)


class UserDetailsApiEventVersion1Component(View):

    def get(self, *args, **kwargs):
        data = {
            "id": self.request.user.id,
            "email": self.request.user.email,
            "firstName": self.request.user.first_name,
            "lastName": self.request.user.last_name,
            "publicName": self.request.user.profile.publicName,
            "jobTitle": self.request.user.profile.jobTitle,
            "department": self.request.user.profile.department,
        }

        response = {
            "success": True,
            "data": data
        }
        return JsonResponse(response, status=HTTPStatus.OK)

    def put(self, *args, **kwargs):
        put = json.loads(self.request.body)

        self.request.user.first_name = put.get("firstName")
        self.request.user.last_name = put.get("lastName")
        self.request.user.profile.publicName = put.get("publicName")
        self.request.user.profile.jobTitle = put.get("jobTitle")
        self.request.user.profile.department = put.get("department")

        self.request.user.save()
        self.request.user.profile.save()

        response = {
            "success": True,
        }
        return JsonResponse(response, status=HTTPStatus.OK)


class UserProfilePictureApiEventVersion1Component(View):

    def get(self, *args, **kwargs):

        try:
            profile = self.request.user.profile
        except Profile.DoesNotExist:
            profile = None

        if not self.request.user or not profile:
            response = {
                "success": False,
            }
            return JsonResponse(response, status=HTTPStatus.OK)

        response = {
            "success": True,
            "data": {
                "id": self.request.user.id,
                "profileId": profile.id,
                "picture": profile.profilePicture.url if profile.profilePicture else None
            }
        }
        return JsonResponse(response, status=HTTPStatus.OK)

    def put(self, *args, **kwargs):

        try:
            profile = self.request.user.profile
        except Profile.DoesNotExist:
            profile = None

        if profile is not None:
            generalOperations.deleteImage(profile.profilePicture)
            profile.profilePicture = generalOperations.getRandomAvatar()
            profile.save(update_fields=['profilePicture'])

        response = {
            "success": True
        }
        return JsonResponse(response, status=HTTPStatus.OK)


class ComponentByComponentGroupObjectApiEventVersion1Component(View):

    def get(self, *args, **kwargs):
        attribute = self.kwargs.get("attribute")

        querySet = Q(componentGroup__internalKey__icontains=attribute) | Q(componentGroup__code__icontains=attribute)

        if attribute.isnumeric():
            querySet = querySet | Q(componentGroup_id=attribute)

        componentList = Component.objects.filter(querySet)

        response = {
            "success": True,
            "data": {
                "components": [
                    component.serializeComponentVersion1()
                    for component in componentList
                ]
            }
        }
        return JsonResponse(response, status=HTTPStatus.OK)
