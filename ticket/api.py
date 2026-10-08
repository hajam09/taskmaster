from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Count, Exists, OuterRef, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core import service
from core.models import ColumnStatus, Label, Ticket, TicketComment, TicketLink
from core.serializers import (
    EpicIssueAttachSerializer,
    EpicIssueCreateSerializer,
    TicketCommentSerializer,
    TicketInlineUpdateSerializer,
    TicketLinkCreateSerializer,
    TicketSubTaskAttachSerializer,
    TicketSubTaskCreateSerializer,
    TicketSubTaskSerializer,
)

MAN_AVATAR = 'https://cdn3.iconfinder.com/data/icons/avatars-round-flat/33/man5-512.png'


class TicketOrderNoUpdateApiV1(APIView):
    def put(self, *args, **kwargs):
        tickets = list(Ticket.objects.filter(id__in=self.request.data))
        orderedTickets = service.updateOrderNoForListOfObjects(tickets, self.request.data)
        Ticket.objects.bulk_update(orderedTickets, ['orderNo'])
        return Response(status=status.HTTP_200_OK)


class UserLiveSearchApiVersion1(APIView):
    limit = 10

    def get_queryset(self):
        query = self.request.query_params.get('query', '').strip()
        users = User.objects.only('id', 'first_name', 'last_name').order_by('first_name', 'last_name')
        if not query:
            return users[:self.limit]
        filters = Q(first_name__icontains=query) | Q(last_name__icontains=query)
        return users.filter(filters)[:self.limit]

    def get(self, request, *args, **kwargs):
        data = [
            {
                'id': user.id,
                'name': f'{user.first_name} {user.last_name}'.strip(),
                'icon': MAN_AVATAR,
            }
            for user in self.get_queryset()
        ]
        return Response(data, status=status.HTTP_200_OK)


class LabelLiveSearchApiVersion1(APIView):
    limit = 10

    def get_queryset(self):
        query = self.request.query_params.get('query', '').strip()
        labels = Label.objects.only('id', 'name', 'colour').order_by('name')
        if not query:
            return labels[:self.limit]
        return labels.filter(name__icontains=query)[:self.limit]

    def get(self, request, *args, **kwargs):
        data = [
            {
                'id': label.id,
                'name': label.name,
                'colour': label.colour,
            }
            for label in self.get_queryset()
        ]
        return Response(data, status=status.HTTP_200_OK)


class TicketLiveSearchApiVersion1(APIView):
    limit = 10

    def get_queryset(self):
        query = self.request.query_params.get('query', '').strip()
        subTaskOnly = self.request.query_params.get('subTaskOnly', '').strip().lower() == 'true'
        excludeTicketIds = self.request.query_params.getlist('excludeTicketIds')
        epicOnly = self.request.query_params.get('epicOnly', '').strip().lower() == 'true'
        excludeEpic = self.request.query_params.get('excludeEpic', '').strip().lower() == 'true'

        tickets = Ticket.objects.only('id', 'url', 'summary', 'type').order_by('url')
        if subTaskOnly:
            tickets = tickets.filter(type=Ticket.Type.SUB_TASK)
        if epicOnly:
            tickets = tickets.filter(type=Ticket.Type.EPIC)
        if excludeEpic:
            tickets = tickets.exclude(type=Ticket.Type.EPIC)
        if excludeTicketIds:
            tickets = tickets.exclude(id__in=excludeTicketIds)
        if not query:
            return tickets[:self.limit]

        filters = Q(url__icontains=query) | Q(summary__icontains=query)
        return tickets.filter(filters)[:self.limit]

    def get(self, request, *args, **kwargs):
        data = [
            {
                'id': ticket.id,
                'url': ticket.url,
                'icon': ticket.ticketTypeIcon,
                'summary': ticket.summary,
            }
            for ticket in self.get_queryset()
        ]
        return Response(data, status=status.HTTP_200_OK)


class TicketApiVersion1(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        ticket = get_object_or_404(
            Ticket.objects.select_related(
                'project', 'assignee', 'reporter', 'columnStatus__column', 'epic',
            ).prefetch_related('label'),
            url=request.query_params.get('url'),
        )
        assignee = ticket.assignee
        columnStatus = ticket.columnStatus
        epic = ticket.epic

        data = {
            'id': ticket.id,
            'url': ticket.url,
            'href': ticket.getUrl,
            'summary': ticket.summary,
            'description': service.sanitiseTicketDescription(ticket.description),
            'storyPoints': ticket.storyPoints,
            'createdDateTime': ticket.createdDateTime,
            'modifiedDateTime': ticket.modifiedDateTime,
            'project': {
                'id': ticket.project.id,
                'name': ticket.project.name,
                'icon': ticket.project.icon,
            },
            'type': {
                'name': ticket.get_type_display(),
                'value': ticket.type,
                'icon': ticket.typeIcon,
            },
            'priority': {
                'name': ticket.get_priority_display(),
                'value': ticket.priority,
                'icon': ticket.priorityIcon,
            },
            'reporter': {
                'id': ticket.reporter.id,
                'name': ticket.reporter.get_full_name(),
                'icon': MAN_AVATAR,
            },
            'assignee': None,
            'resolution': {
                'name': ticket.get_resolution_display(),
                'value': ticket.resolution,
            },
            'epic': None,
            'label': [
                {'id': label.id, 'name': label.name, 'colour': label.colour}
                for label in ticket.label.all()
            ],
            'editOptions': {
                'type': [
                    {'key': value, 'value': label, 'icon': Ticket.icons.get(value)}
                    for value, label in Ticket.Type.choices
                ],
                'priority': [
                    {'key': value, 'value': label, 'icon': Ticket.icons.get(value)}
                    for value, label in Ticket.Priority.choices
                ],
                'resolution': [
                    {'key': value, 'value': label}
                    for value, label in Ticket.Resolution.choices
                ],
                'columnStatus': [
                    {
                        'key': item.id,
                        'value': item.name,
                        'colour': item.column.getColour(),
                    }
                    for item in ColumnStatus.objects.filter(
                        column__board_id=ticket.columnStatus.column.board_id
                    ).order_by('orderNo')
                ],
            },
            'team': None,
            'sprint': None,
            'votes': 2,
            'watchers': 4,
        }

        if assignee:
            data['assignee'] = {
                'id': assignee.id,
                'name': assignee.get_full_name(),
                'icon': MAN_AVATAR,
            }
        if columnStatus:
            column = columnStatus.column
            data['columnStatus'] = {
                'id': columnStatus.id,
                'name': columnStatus.name,
                'column': {
                    'id': column.id,
                    'name': column.name,
                    'colour': column.getColour(),
                } if column else None,
            }
        else:
            data['columnStatus'] = None
        if epic:
            data['epic'] = {
                'id': epic.id,
                'url': epic.url,
                'href': epic.getUrl,
                'summary': epic.summary,
                'icon': epic.typeIcon,
            }
        return Response(data=data, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        ticket = get_object_or_404(Ticket, url=request.query_params.get('url'))
        serializer = TicketInlineUpdateSerializer(ticket, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.get(request, *args, **kwargs)


class EpicIssueListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TicketSubTaskSerializer

    def getEpicTicket(self):
        if not hasattr(self, 'epic'):
            idOrUrl = self.kwargs['ticketIdOrUrl']
            self.epic = get_object_or_404(
                Ticket.objects.select_related('project', 'columnStatus__column'),
                Q(id=int(idOrUrl)) | Q(url=idOrUrl) if idOrUrl.isdigit() else Q(url=idOrUrl),
                type=Ticket.Type.EPIC,
            )
        return self.epic

    def get_queryset(self):
        return self.getEpicTicket().epicTickets.select_related('columnStatus__column').order_by('orderNo')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            if 'ticketIds' in self.request.data:
                return EpicIssueAttachSerializer
            return EpicIssueCreateSerializer
        return TicketSubTaskSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['ticket'] = self.getEpicTicket()
        return context

    def create(self, request, *args, **kwargs):
        # 5 queries for new subtask, 4 queries for attach existing subtasks
        attaching = 'ticketIds' in request.data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if attaching:
            Ticket.objects.filter(id__in=serializer.validated_data['ticketIds']).update(epic=self.getEpicTicket())
            return Response(TicketSubTaskSerializer(self.get_queryset(), many=True).data, status=status.HTTP_200_OK)
        issue = serializer.save()
        return Response(TicketSubTaskSerializer(issue).data, status=status.HTTP_201_CREATED)


class TicketSubTaskListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TicketSubTaskSerializer

    def getTicket(self):
        if not hasattr(self, 'ticket'):
            idOrUrl = self.kwargs['ticketIdOrUrl']
            self.ticket = get_object_or_404(
                Ticket.objects.select_related('project', 'columnStatus__column'),
                Q(id=int(idOrUrl)) | Q(url=idOrUrl) if idOrUrl.isdigit() else Q(url=idOrUrl)
            )
        return self.ticket

    def get_queryset(self):
        # 3 queries
        return self.getTicket().subTasks.select_related('columnStatus__column').order_by('orderNo')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            if 'ticketIds' in self.request.data:
                return TicketSubTaskAttachSerializer
            return TicketSubTaskCreateSerializer
        return TicketSubTaskSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['ticket'] = self.getTicket()
        return context

    def create(self, request, *args, **kwargs):
        # 5 queries for new subtask, 4 queries for attach existing subtasks
        attaching = 'ticketIds' in request.data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if attaching:
            Ticket.objects.filter(id__in=serializer.validated_data['ticketIds']).update(parent=self.getTicket())
            return Response(TicketSubTaskSerializer(self.get_queryset(), many=True).data, status=status.HTTP_200_OK)
        subtask = serializer.save()
        return Response(TicketSubTaskSerializer(subtask).data, status=status.HTTP_201_CREATED)


class TicketLinkedIssueListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    ticket = None

    def getTicket(self):
        if not hasattr(self, 'ticket'):
            idOrUrl = self.kwargs['ticketIdOrUrl']
            self.ticket = get_object_or_404(
                Ticket,
                Q(id=int(idOrUrl)) | Q(url=idOrUrl) if idOrUrl.isdigit() else Q(url=idOrUrl)
            )
        return self.ticket

    def getResponseData(self):
        return [
            {
                'linkType': linkType,
                'tickets': TicketSubTaskSerializer(tickets, many=True).data,
            }
            for linkType, tickets in service.groupLinkedIssues(self.getTicket()).items()
        ]

    def get(self, request, *args, **kwargs):
        # 2 queries
        return Response(self.getResponseData(), status=status.HTTP_200_OK)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        # 4 queries
        serializer = TicketLinkCreateSerializer(data=request.data, context={'ticket': self.getTicket()})
        serializer.is_valid(raise_exception=True)
        links = [
            TicketLink(
                source=self.getTicket(),
                target_id=target,
                linkType=serializer.validated_data['linkType'],
            )
            for target in serializer.validated_data['ticketIds']
        ]
        TicketLink.objects.bulk_create(links, ignore_conflicts=True)
        return Response(self.getResponseData(), status=status.HTTP_201_CREATED)


class TicketCommentQuerysetMixin:
    def get_queryset(self):
        return (
            TicketComment.objects.filter(ticket__id=self.kwargs['ticketId']).select_related('creator')
            .annotate(
                likes_count=Count('likes', distinct=True),
                dislikes_count=Count('dislikes', distinct=True),
                in_likes=Exists(
                    TicketComment.likes.through.objects.filter(
                        ticketcomment_id=OuterRef('pk'),
                        user_id=self.request.user.id,
                    )
                ),
                in_dislikes=Exists(
                    TicketComment.dislikes.through.objects.filter(
                        ticketcomment_id=OuterRef('pk'),
                        user_id=self.request.user.id,
                    )
                ),
            )
        )


class TicketCommentListCreateView(TicketCommentQuerysetMixin, generics.ListCreateAPIView):
    serializer_class = TicketCommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return super().get_queryset().order_by('-createdDateTime')

    def perform_create(self, serializer):
        ticket = get_object_or_404(Ticket, id=self.kwargs['ticketId'])
        serializer.save(creator=self.request.user, ticket=ticket)


class TicketCommentDetailView(TicketCommentQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TicketCommentSerializer
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):
        if self.get_object().creator != self.request.user:
            raise PermissionDenied('You can only edit your own comments.')
        serializer.save(edited=True)

    def post(self, request, *args, **kwargs):
        comment = self.get_object()
        reaction = request.data.get('reaction')
        if reaction == 'like':
            comment.like(request)
        elif reaction == 'dislike':
            comment.dislike(request)
        else:
            return Response({'reaction': 'Choose either "like" or "dislike".'}, status=status.HTTP_400_BAD_REQUEST)
        comment = self.get_queryset().get(pk=comment.pk)
        return Response(self.get_serializer(comment).data, status=status.HTTP_200_OK)

    def perform_destroy(self, instance):
        if instance.creator != self.request.user:
            raise PermissionDenied('You can only delete your own comments.')
        instance.delete()
