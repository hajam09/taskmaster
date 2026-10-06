import json

from django.contrib import messages
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core import service
from core.models import (
    ColumnStatus,
    Column,
    Label,
    Project,
    Ticket,
    Sprint
)
from core.serializers import (
    TicketInlineUpdateSerializer,
    TicketSerializerVersion1,
    sanitize_ticket_description,
)

MAN_AVATAR = 'https://cdn3.iconfinder.com/data/icons/avatars-round-flat/33/man5-512.png'


class BoardColumnAndStatusApiVersion1(APIView):

    @transaction.atomic
    def put(self, *args, **kwargs):
        data = self.request.data

        columnIds = []
        statusIds = []

        for col in data:
            columnIds.append(int(col['column-id']))
            for st in col.get('status-data', []):
                statusIds.append(int(st['column-status-id']))

        columns = Column.objects.select_for_update().in_bulk(columnIds)
        columnStatuses = ColumnStatus.objects.select_for_update().in_bulk(statusIds)

        columnsToUpdate = []
        columnStatusesToUpdate = []

        for columnData in data:
            column = columns.get(int(columnData['column-id']))
            column.name = columnData['column-name']
            columnsToUpdate.append(column)

            for columnStatusData in columnData.get('status-data', []):
                columnStatus = columnStatuses.get(int(columnStatusData['column-status-id']))
                columnStatus.name = columnStatusData['column-status-name']
                columnStatusesToUpdate.append(columnStatus)

        orderedColumns = service.updateOrderNoForListOfObjects(columnsToUpdate, columnIds)
        orderedStatuses = service.updateOrderNoForListOfObjects(columnStatusesToUpdate, statusIds)
        Column.objects.bulk_update(orderedColumns, ['name', 'orderNo'])
        ColumnStatus.objects.bulk_update(orderedStatuses, ['name', 'orderNo'])
        return Response(status=status.HTTP_200_OK)


class TicketColumStatusApiVersion1(APIView):

    @transaction.atomic
    def put(self, *args, **kwargs):
        columnStatusId = self.request.data.get('column-status-id')
        ticketIds = self.request.data.get('ticket-ids')

        tickets = list(Ticket.objects.filter(id__in=ticketIds))
        orderedTickets = service.updateOrderNoForListOfObjects(tickets, ticketIds)

        for ticket in orderedTickets:
            ticket.columnStatus_id = columnStatusId

        Ticket.objects.bulk_update(tickets, ['columnStatus', 'orderNo'])
        return Response(status=status.HTTP_200_OK)


class TicketOrderNoUpdateApiV1(APIView):
    def put(self, *args, **kwargs):
        tickets = list(Ticket.objects.filter(id__in=self.request.data))
        orderedTickets = service.updateOrderNoForListOfObjects(tickets, self.request.data)
        Ticket.objects.bulk_update(orderedTickets, ['orderNo'])
        return Response(status=status.HTTP_200_OK)


class ScrumBoardBacklogTicketUpdateApiVersion1(APIView):

    @transaction.atomic
    def put(self, *args, **kwargs):
        zone = self.request.data.get('zone')
        ticketIds = self.request.data.get('tickets', [])

        Sprint.tickets.through.objects.filter(ticket_id__in=ticketIds).delete()
        tickets = list(Ticket.objects.filter(id__in=ticketIds))

        if zone == 'sprint':
            sprint = Sprint.objects.select_related('board').get(id=self.request.data.get('sprint-id'))
            sprint.tickets.add(*ticketIds)

            columnStatus = ColumnStatus.objects.filter(
                column__board=sprint.board,
                column__status=Column.Status.TODO
            ).order_by('id').first()

            for ticket in tickets:
                ticket.columnStatus = columnStatus

        elif zone == 'backlog':
            columnStatusId = self.request.data.get('column-id')
            for ticket in tickets:
                ticket.columnStatus_id = columnStatusId

        orderedTickets = service.updateOrderNoForListOfObjects(tickets, ticketIds)
        Ticket.objects.bulk_update(orderedTickets, ['orderNo'])
        return Response(status=status.HTTP_200_OK)


class StartSprintEventApiVersion1(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sprint = None

    def dispatch(self, request, *args, **kwargs):
        self.sprint = Sprint.objects.get(
            id=json.loads(request.body.decode('utf-8')).get('sprint-id')
        )
        return super().dispatch(request, *args, **kwargs)

    def startSprintConditions(self):
        condition1 = {
            'board': self.sprint.board,
            'isActive': True
        }
        conditions2 = {
            'board': self.sprint.board,
            'isComplete': False,
            'id__lt': self.sprint.id
        }

        if not self.sprint.tickets.exists():
            return 'Selected sprint does not have any tickets. Please add ticket(s) before starting the sprint.'
        if Sprint.objects.filter(**condition1).exclude(id=self.sprint.id).exists():
            return 'Please complete your existing sprint before starting a new one.'
        if Sprint.objects.filter(**conditions2).exclude(id=self.sprint.id).exists():
            return 'You have an ongoing or incomplete sprint. Please finish it before moving on to the next one.'
        return None

    def put(self, request, *args, **kwargs):
        sprintConditions = self.startSprintConditions()
        if sprintConditions is None:
            self.sprint.isActive = True
            self.sprint.save()
        else:
            messages.error(request, sprintConditions)
        return Response(status=status.HTTP_200_OK)


class CompleteSprintEventApiVersion1(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sprint = None
        self.onGoingColumnStatus = None

    def dispatch(self, request, *args, **kwargs):
        self.sprint = Sprint.objects.get(
            id=json.loads(request.body.decode('utf-8')).get('sprint-id')
        )
        self.onGoingColumnStatus = [Column.Status.TODO, Column.Status.IN_PROGRESS]
        return super().dispatch(request, *args, **kwargs)

    @transaction.atomic
    def put(self, request, *args, **kwargs):
        incompleteTickets = self.sprint.tickets.filter(columnStatus__column__status__in=self.onGoingColumnStatus)
        nextSprint = Sprint.objects.filter(
            board=self.sprint.board,
            isComplete=False,
            isActive=False
        ).order_by('id').exclude(id=self.sprint.id).first()

        if nextSprint is None:
            columnStatus = ColumnStatus.objects.filter(
                column__board=self.sprint.board, column__status=Column.Status.BACK_LOG
            ).order_by('id')[:1].first()
            incompleteTickets.update(columnStatus=columnStatus)
            messages.success(
                request,
                f'{self.sprint.name} has been completed and incomplete tickets has been moved to the backlog!'
            )
        else:
            nextSprint.tickets.add(*incompleteTickets)
            nextSprint.isActive = True
            nextSprint.save()
            messages.success(
                request,
                f'{self.sprint.name} has been completed and incomplete tickets has been moved to {nextSprint.name}!'
            )

        self.sprint.tickets.remove(*incompleteTickets)
        self.sprint.isComplete = True
        self.sprint.isActive = False
        self.sprint.save()
        return Response(status=status.HTTP_200_OK)


class TicketTypeListApiVersion1(APIView):
    def get(self, *args, **kwargs):
        data = [
            {
                'key': item,
                'value': item.label,
                'icon': Ticket.icons.get(item),
            }
            for item in Ticket.Type
        ]
        data = sorted(data, key=lambda x: x['value'].lower())
        return Response(data=data, status=status.HTTP_200_OK)


class TicketPriorityListApiVersion1(APIView):
    def get(self, *args, **kwargs):
        data = [
            {
                'key': item,
                'value': item.label,
                'icon': Ticket.icons.get(item),
            }
            for item in Ticket.Priority
        ]
        data = sorted(data, key=lambda x: x['value'].lower())
        return Response(data=data, status=status.HTTP_200_OK)


class ColumnStatusListApiVersion1(APIView):
    def get(self, *args, **kwargs):
        data = [
            {
                'key': item,
                'value': item,
            }
            for item in ColumnStatus.objects.order_by('name').values_list('name', flat=True)
        ]
        return Response(data=data, status=status.HTTP_200_OK)


class ResolutionListApiVersion1(APIView):
    def get(self, *args, **kwargs):
        data = [
            {
                'key': item,
                'value': item.label,
            }
            for item in Ticket.Resolution
        ]
        data = sorted(data, key=lambda x: x['value'].lower())
        return Response(data=data, status=status.HTTP_200_OK)


class ProjectListApiVersion1(APIView):
    def get(self, *args, **kwargs):
        data = [
            {
                'key': item['code'],
                'value': item['name']
            }
            for item in Project.objects.order_by('name').values('code', 'name')
        ]
        return Response(data=data, status=status.HTTP_200_OK)


class UserListApiVersion1(APIView):
    def get(self, *args, **kwargs):
        data = [
            {
                'key': item.id,
                'value': f"{item.first_name} {item.last_name}".strip()
            }
            for item in User.objects.order_by('first_name', 'last_name').only('id', 'first_name', 'last_name')
        ]
        return Response(data=data, status=status.HTTP_200_OK)


class ProjectStatusListApiVersion1(APIView):
    def get(self, *args, **kwargs):
        data = [
            {
                'key': item,
                'value': item.label,
            }
            for item in Project.Status
        ]
        data = sorted(data, key=lambda x: x['value'].lower())
        return Response(data=data, status=status.HTTP_200_OK)


class LabelListApiVersion1(APIView):
    def get(self, *args, **kwargs):
        data = [
            {
                'key': item,
                'value': item,
            }
            for item in Label.objects.order_by('name').values_list('name', flat=True)
        ]
        return Response(data=data, status=status.HTTP_200_OK)


class UserLiveSearchApiVersion1(APIView):
    limit = 20
    initial_limit = 10

    def get_queryset(self):
        query = self.request.query_params.get('query', '').strip()
        users = User.objects.only(
            'id', 'first_name', 'last_name', 'username'
        ).order_by('first_name', 'last_name', 'username')
        if not query:
            return users[:self.initial_limit]

        filters = Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(username__icontains=query)
        return users.filter(filters)[:self.limit]

    def get(self, request, *args, **kwargs):
        data = [
            {
                'id': user.id,
                'name': f"{user.first_name} {user.last_name}".strip(),
                'icon': MAN_AVATAR,
            }
            for user in self.get_queryset()
        ]

        return Response(data, status=status.HTTP_200_OK)


class LabelLiveSearchApiVersion1(APIView):
    limit = 20
    initial_limit = 10

    def get_queryset(self):
        query = self.request.query_params.get('query', '').strip()
        labels = Label.objects.only('id', 'name', 'colour').order_by('name')
        if not query:
            return labels[:self.initial_limit]
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
    limit = 20
    initial_limit = 10

    def get_queryset(self):
        query = self.request.query_params.get('query', '').strip()
        subTaskOnly = self.request.query_params.get('subTaskOnly', '').strip().lower() == 'true'
        tickets = Ticket.objects.only('id', 'url', 'summary', 'type').order_by('url')
        if subTaskOnly:
            tickets = tickets.filter(type=Ticket.Type.SUB_TASK)
        if not query:
            return tickets[:self.initial_limit]

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
        ticket = get_object_or_404(Ticket.objects.select_related(
            'project', 'assignee', 'reporter', 'columnStatus__column', 'epic',
        ).prefetch_related('label'), url=request.query_params.get('url'))

        assignee = ticket.assignee
        columnStatus = ticket.columnStatus
        epic = ticket.epic

        data = {
            'id': ticket.id,
            'url': ticket.url,
            'href': ticket.getUrl,
            'summary': ticket.summary,
            'description': sanitize_ticket_description(ticket.description),
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
            'label': [
                {
                    'id': l.id,
                    'name': l.name,
                    'colour': l.colour,
                }
                for l in ticket.label.all()
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
            data.update({
                'assignee': {
                    'id': ticket.assignee.id,
                    'name': assignee.get_full_name(),
                    'icon': MAN_AVATAR
                },
            })

        if columnStatus:
            column = columnStatus.column
            columnStatus = {
                'id': columnStatus.id,
                'name': columnStatus.name
            }

            if column:
                columnStatus.update({
                    'column': {
                        'id': column.id,
                        'name': column.name,
                        'colour': column.getColour(),
                    }
                })
            data.update({
                'columnStatus': columnStatus
            })
        else:
            data['columnStatus'] = None

        if epic:
            data.update({
                'epic': {
                    'id': epic.id,
                    'url': epic.url,
                    'href': epic.getUrl,
                    'summary': epic.summary,
                    'icon': epic.typeIcon,
                }
            })
        return Response(data=data, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        ticket = get_object_or_404(Ticket, url=request.query_params.get('url'))
        serializer = TicketInlineUpdateSerializer(
            ticket,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.get(request, *args, **kwargs)
