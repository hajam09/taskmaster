# from django.contrib.auth.models import User
# from django.core.cache import cache
# from django.core.exceptions import PermissionDenied
# from django.db.models import Q
# from rest_framework import viewsets, status
# from rest_framework.response import Response
#
# from accounts.models import Team, Profile
# from api.serializers import BoardSerializerVersion1, TeamSerializerVersion1, ProjectSerializerVersion1, \
#     TicketSerializerVersion1, UserSerializerVersion1
# from jira.models import Board, Project, Ticket
#
#
# class TeamModelViewSetApiVersion1(viewsets.ModelViewSet):
#     queryset = Team.objects.all().prefetch_related('admins__profile', 'members__profile')
#     serializer_class = TeamSerializerVersion1
#
#     def get_object(self):
#         return self.get_queryset().get(url=self.kwargs['url'])
#
#     def list(self, request, *args, **kwargs):
#         teams = self.get_queryset()
#         serializers = self.get_serializer(teams, many=True)
#         return Response(serializers.data)
#
#     def retrieve(self, request, *args, **kwargs):
#         try:
#             team = self.get_object()
#         except Team.DoesNotExist:
#             return Response(
#                 data={'error': f'Team {kwargs.get("url")} is not found.'}, status=status.HTTP_404_NOT_FOUND
#             )
#
#         if not team.hasAccessPermission(request.user):
#             raise PermissionDenied()
#
#         serializers = self.get_serializer(team)
#         return Response(serializers.data)
#
#     def create(self, request, *args, **kwargs):
#         internalKey = request.data.get('internalKey')
#         if Team.objects.filter(internalKey=internalKey).exists():
#             return Response(
#                 data={'error': f'Team with name {internalKey} already exists.'}, status=status.HTTP_400_BAD_REQUEST
#             )
#
#         team = Team()
#         team.internalKey = internalKey
#         team.description = request.data.get("description")
#         team.isPrivate = request.data.get("isPrivate")
#         team.save()
#
#         team.admins.add(*request.data.get('admins'))
#         team.members.add(*request.data.get('members'))
#         return Response(status=status.HTTP_200_OK)
#
#
# class BoardModelViewSetApiVersion1(viewsets.ModelViewSet):
#     queryset = Board.objects.all().prefetch_related('projects__status', 'projects__lead', 'admins', 'members')
#     serializer_class = BoardSerializerVersion1
#
#     def get_object(self):
#         return self.get_queryset().get(url=self.kwargs['url'])
#
#     def list(self, request, *args, **kwargs):
#         boards = self.get_queryset()
#         serializers = self.get_serializer(boards, many=True)
#         return Response(serializers.data)
#
#     def retrieve(self, request, *args, **kwargs):
#         instance = self.get_object()
#         serializers = self.get_serializer(instance)
#         return Response(serializers.data)
#
#
# class ProjectModelViewSetApiVersion1(viewsets.ModelViewSet):
#     serializer_class = ProjectSerializerVersion1
#
#     def get_queryset(self):
#         # Project.objects.filter(
#         #     Q(isPrivate=True, members__in=[self.request.user]) | Q(isPrivate=False)
#         # ).distinct().select_related('status', 'lead')
#         return Project.objects.filter(
#             Q(isPrivate=True) | Q(isPrivate=False)
#         ).distinct().select_related('status', 'lead')
#
#     def get_object(self):
#         return self.get_queryset().get(url=self.kwargs['url'])
#
#     def list(self, request, *args, **kwargs):
#         projects = self.get_queryset()
#         serializers = self.get_serializer(projects, many=True)
#         return Response(serializers.data)
#
#     def retrieve(self, request, *args, **kwargs):
#         instance = self.get_object()
#         serializers = self.get_serializer(instance)
#         return Response(serializers.data)
#
#
# from django.db.models import Count
#
#
# class TicketModelViewSetApiVersion1(viewsets.ModelViewSet):
#     serializer_class = TicketSerializerVersion1
#
#     def retrieve(self, request, *args, **kwargs):
#         instance = Ticket.objects.get(internalKey__iexact=self.kwargs['internalKey'])
#         serializers = self.get_serializer(instance)
#         return Response(serializers.data)
#
#
# class DashboardViewSetApiVersion1(viewsets.ViewSet):
#     def list(self, request):
#         ticketsByIssueType = list(Ticket.objects.values(
#             "issueType_id", "issueType__internalKey", "issueType__code", "issueType__icon"
#         ).annotate(count=Count('issueType')))
#
#         ticketsByPriority = list(Ticket.objects.values(
#             "priority_id", "priority__internalKey", "priority__code", "priority__icon"
#         ).annotate(count=Count('priority')))
#
#         for issueType in cache.get('TICKET_ISSUE_TYPE'):
#             found = next((o for o in ticketsByIssueType if o["issueType_id"] == issueType.id), None)
#             if found is None:
#                 ticketsByIssueType.append(
#                     {
#                         'issueType_id': issueType.id,
#                         'issueType__internalKey': issueType.internalKey,
#                         'issueType__code': issueType.code,
#                         'issueType__icon': issueType.icon,
#                         'count': 0
#                     }
#                 )
#
#         for priority in cache.get('TICKET_PRIORITY'):
#             found = next((o for o in ticketsByPriority if o["priority_id"] == priority.id), None)
#             if found is None:
#                 ticketsByPriority.append(
#                     {
#                         'priority_id': priority.id,
#                         'priority__internalKey': priority.internalKey,
#                         'priority__code': priority.code,
#                         'priority__icon': priority.icon,
#                         'count': 0
#                     }
#                 )
#
#         return Response({"ticketsByIssueType": ticketsByIssueType, "ticketsByPriority": ticketsByPriority})
#
#
# class TeamViewSetApiVersion1(viewsets.ViewSet):
#     def retrieve(self, request, *args, **kwargs):
#         team = Team.objects.prefetch_related('admins__profile', 'members__profile').get(url=kwargs.get("url"))
#
#         if not team.hasAccessPermission(request.user):
#             raise PermissionDenied()
#
#         teamSerializer = TeamSerializerVersion1(team)
#
#         memberIds = team.members.values_list('id', flat=True)
#         adminIds = team.admins.values_list('id', flat=True)
#         uniqueAssociates = (team.members.all() | team.admins.all()).distinct()
#
#         teamTickets = Ticket.objects.filter(
#             Q(assignee__in=uniqueAssociates) | Q(reporter_id__in=uniqueAssociates)
#         ).select_related('priority', 'issueType', 'assignee__profile').order_by('-modifiedDateTime')[:5]
#
#         ticketSerializer = TicketSerializerVersion1(teamTickets, many=True)
#
#         userList = User.objects.all().prefetch_related("profile")
#         otherMembers = UserSerializerVersion1(userList.exclude(id__in=memberIds), many=True)
#         otherAdmins = UserSerializerVersion1(userList.exclude(id__in=adminIds), many=True)
#
#         data = {
#             "team": teamSerializer.data,
#             "otherMembers": otherMembers.data,
#             "otherAdmins": otherAdmins.data,
#             "teamTickets": ticketSerializer.data,
#             "hasChatPermission": request.user in uniqueAssociates,
#         }
#         return Response(data, status=status.HTTP_200_OK)