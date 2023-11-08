# from django.conf import settings
# from django.contrib.auth.models import User
# from rest_framework import serializers
#
# from accounts.models import Profile, Team, Component
# from jira.models import Board, Project, Ticket
#
#
# class UserModelSerializerVersion1(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ["id", "first_name", "last_name"]
#
#
# class UserAndProfileModelSerializerVersion1(serializers.ModelSerializer):
#     url = serializers.SerializerMethodField()
#     jobTitle = serializers.SerializerMethodField()
#     department = serializers.SerializerMethodField()
#     icon = serializers.SerializerMethodField()
#
#     def get_url(self, user):
#         try:
#             profile = user.profile
#             return profile.url
#         except Profile.DoesNotExist:
#             return None
#
#     def get_jobTitle(self, user):
#         try:
#             profile = user.profile
#             return profile.jobTitle
#         except Profile.DoesNotExist:
#             return None
#
#     def get_department(self, user):
#         try:
#             profile = user.profile
#             return profile.department
#         except Profile.DoesNotExist:
#             return None
#
#     def get_icon(self, user):
#         try:
#             profile = user.profile
#             return profile.profilePicture.url
#         except Profile.DoesNotExist:
#             return None
#
#     class Meta:
#         model = User
#         fields = ["id", "first_name", "last_name", "url", "jobTitle", "department", "icon"]
#
#
# # class TeamSerializerVersion1(serializers.ModelSerializer):
# #     admins = UserSerializerVersion1(read_only=True, many=True)
# #     members = UserSerializerVersion1(read_only=True, many=True)
# #
# #     class Meta:
# #         model = Team
# #         fields = ["id", "internalKey", "url", "description", "isPrivate", "admins", "members"]
# #
# #
# # class ComponentSerializerVersion1(serializers.ModelSerializer):
# #     class Meta:
# #         model = Component
# #         exclude = ("createdDateTime", "modifiedDateTime", "componentGroup",)
# #
# #
# # class ProjectSerializerVersion1(serializers.ModelSerializer):
# #     icon = serializers.SerializerMethodField()
# #     lead = UserSerializerVersion1(read_only=True, many=False)
# #     status = ComponentSerializerVersion1(read_only=True, many=False)
# #
# #     def get_icon(self, project):
# #         if settings.DEBUG:
# #             return None
# #         return project.icon.url
# #
# #     class Meta:
# #         model = Project
# #         fields = ["id", "internalKey", "url", "icon", "code", "lead", "status"]
# #
# #
# # class BoardSerializerVersion1(serializers.ModelSerializer):
# #     projects = ProjectSerializerVersion1(read_only=True, many=True)
# #     admins = UserSerializerVersion1(read_only=True, many=True)
# #     members = UserSerializerVersion1(read_only=True, many=True)
# #
# #     class Meta:
# #         model = Board
# #         fields = ["id", "url", "internalKey", "type", "isPrivate", "projects", "admins", "members"]
# #
# #
# # class TicketSerializerVersion1(serializers.ModelSerializer):
# #     issueType = ComponentSerializerVersion1(read_only=True, many=False)
# #     priority = ComponentSerializerVersion1(read_only=True, many=False)
# #     assignee = UserSerializerVersion1(read_only=True, many=False)
# #
# #     class Meta:
# #         model = Ticket
# #         fields = "__all__"
