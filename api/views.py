from django.core.cache import cache
from django.db.models import Q
from rest_framework import viewsets
from rest_framework.response import Response

from accounts.models import Team
from api.serializers import BoardSerializerVersion1, TeamSerializerVersion1, ProjectSerializerVersion1, \
    TicketSerializerVersion1
from jira.models import Board, Project, Ticket, ProjectComponent


class TeamModelViewSetApiVersion1(viewsets.ModelViewSet):
    queryset = Team.objects.all().prefetch_related('admins', 'members')
    serializer_class = TeamSerializerVersion1

    def get_object(self):
        return self.get_queryset().get(url=self.kwargs['url'])

    def list(self, request, *args, **kwargs):
        teams = self.get_queryset()
        serializers = self.get_serializer(teams, many=True)
        return Response(serializers.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializers = self.get_serializer(instance)
        return Response(serializers.data)


class BoardModelViewSetApiVersion1(viewsets.ModelViewSet):
    queryset = Board.objects.all().prefetch_related('projects__status', 'projects__lead', 'admins', 'members')
    serializer_class = BoardSerializerVersion1

    def get_object(self):
        return self.get_queryset().get(url=self.kwargs['url'])

    def list(self, request, *args, **kwargs):
        boards = self.get_queryset()
        serializers = self.get_serializer(boards, many=True)
        return Response(serializers.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializers = self.get_serializer(instance)
        return Response(serializers.data)


class ProjectModelViewSetApiVersion1(viewsets.ModelViewSet):
    serializer_class = ProjectSerializerVersion1

    def get_queryset(self):
        # Project.objects.filter(
        #     Q(isPrivate=True, members__in=[self.request.user]) | Q(isPrivate=False)
        # ).distinct().select_related('status', 'lead')
        return Project.objects.filter(
            Q(isPrivate=True) | Q(isPrivate=False)
        ).distinct().select_related('status', 'lead')

    def get_object(self):
        return self.get_queryset().get(url=self.kwargs['url'])

    def list(self, request, *args, **kwargs):
        projects = self.get_queryset()
        serializers = self.get_serializer(projects, many=True)
        return Response(serializers.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializers = self.get_serializer(instance)
        return Response(serializers.data)


from django.db.models import Count


class TicketModelViewSetApiVersion1(viewsets.ModelViewSet):
    serializer_class = TicketSerializerVersion1

    def retrieve(self, request, *args, **kwargs):
        instance = Ticket.objects.get(internalKey__iexact=self.kwargs['internalKey'])
        serializers = self.get_serializer(instance)
        return Response(serializers.data)


class DashboardViewSetApiVersion1(viewsets.ViewSet):
    def list(self, request):
        ticketsByIssueType = list(Ticket.objects.values(
            "issueType_id", "issueType__internalKey", "issueType__code", "issueType__icon"
        ).annotate(count=Count('issueType')))

        ticketsByPriority = list(Ticket.objects.values(
            "priority_id", "priority__internalKey", "priority__code", "priority__icon"
        ).annotate(count=Count('priority')))

        for issueType in cache.get('TICKET_ISSUE_TYPE'):
            found = next((o for o in ticketsByIssueType if o["issueType_id"] == issueType.id), None)
            if found is None:
                ticketsByIssueType.append(
                    {
                        'issueType_id': issueType.id,
                        'issueType__internalKey': issueType.internalKey,
                        'issueType__code': issueType.code,
                        'issueType__icon': issueType.icon,
                        'count': 0
                    }
                )

        for priority in cache.get('TICKET_PRIORITY'):
            found = next((o for o in ticketsByPriority if o["priority_id"] == priority.id), None)
            if found is None:
                ticketsByPriority.append(
                    {
                        'priority_id': priority.id,
                        'priority__internalKey': priority.internalKey,
                        'priority__code': priority.code,
                        'priority__icon': priority.icon,
                        'count': 0
                    }
                )

        return Response({"ticketsByIssueType": ticketsByIssueType, "ticketsByPriority": ticketsByPriority})


class TeamViewSetApiVersion1(viewsets.ViewSet):
    def retrieve(self, request, *args, **kwargs):
        team = Team.objects.prefetch_related('admins', 'members').get(url=kwargs.get("url"))
        teamSerializer = TeamSerializerVersion1(team)

        uniqueAssociates = (team.members.all() | team.admins.all()).distinct()

        teamTickets = Ticket.objects.filter(
            Q(assignee__in=uniqueAssociates) | Q(reporter_id__in=uniqueAssociates)
        ).select_related('priority', 'issueType', 'assignee__profile').order_by('-modifiedDateTime')[:5]

        ticketSerializer = TicketSerializerVersion1(teamTickets, many=True)

        return Response({"team": teamSerializer.data, "teamTickets": ticketSerializer.data})
