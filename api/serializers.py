from django.conf import settings
from django.contrib.auth.models import User
from rest_framework import serializers

from accounts.models import Profile, Team, Component
from jira.models import Board, Project, Ticket


class UserSerializerVersion1(serializers.ModelSerializer):
    icon = serializers.SerializerMethodField()

    def get_icon(self, obj):
        if settings.DEBUG:
            return None
        try:
            profile = obj.profile
            return profile.profilePicture
        except Profile.DoesNotExist:
            return None

    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "icon"]


class TeamSerializerVersion1(serializers.ModelSerializer):
    admins = UserSerializerVersion1(read_only=True, many=True)
    members = UserSerializerVersion1(read_only=True, many=True)

    class Meta:
        model = Team
        fields = ["id", "url", "internalKey", "admins", "members", "isPrivate", "description"]


class ComponentSerializerVersion1(serializers.ModelSerializer):
    class Meta:
        model = Component
        exclude = ("createdDateTime", "modifiedDateTime", "componentGroup",)


class ProjectSerializerVersion1(serializers.ModelSerializer):
    icon = serializers.SerializerMethodField()
    lead = UserSerializerVersion1(read_only=True, many=False)
    status = ComponentSerializerVersion1(read_only=True, many=False)

    def get_icon(self, project):
        if settings.DEBUG:
            return None
        return project.icon.url

    class Meta:
        model = Project
        fields = ["id", "internalKey", "url", "icon", "code", "lead", "status"]


class BoardSerializerVersion1(serializers.ModelSerializer):
    projects = ProjectSerializerVersion1(read_only=True, many=True)
    admins = UserSerializerVersion1(read_only=True, many=True)
    members = UserSerializerVersion1(read_only=True, many=True)

    class Meta:
        model = Board
        fields = ["id", "url", "internalKey", "type", "isPrivate", "projects", "admins", "members"]


class TicketSerializerVersion1(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = "__all__"
