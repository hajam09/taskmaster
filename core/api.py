from django.contrib import messages
from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import (
    ColumnStatus,
    Column,
    Ticket,
    Sprint
)


class BoardColumnAndStatusApiVersion1(APIView):
    def put(self, request, *args, **kwargs):
        columnIds = [columnData.get('column-id') for columnData in request.data]
        statusIds = [
            columnStatusData.get('column-status-id')
            for columnData in request.data
            for columnStatusData in columnData.get('status-data')
        ]

        columns = Column.objects.filter(id__in=columnIds)
        columnStatuses = ColumnStatus.objects.filter(id__in=statusIds)

        columnsDict = {str(column.id): column for column in columns}
        statusesDict = {str(columnStatus.id): columnStatus for columnStatus in columnStatuses}

        columnsToUpdate = []
        statusesToUpdate = []

        for columnData in request.data:
            column = columnsDict.get(columnData.get('column-id'))
            if column:
                if column.status in [Column.Status.TODO, Column.Status.IN_PROGRESS]:
                    column.name = columnData.get('column-name')
                column.orderNo = columnData.get('order-no')
                columnsToUpdate.append(column)

                for columnStatusData in columnData.get('status-data'):
                    columnStatus = statusesDict.get(columnStatusData.get('column-status-id'))
                    if columnStatus:
                        columnStatus.name = columnStatusData.get('column-status-name')
                        columnStatus.orderNo = columnStatusData.get('order-no')
                        statusesToUpdate.append(columnStatus)

        with transaction.atomic():
            if columnsToUpdate:
                Column.objects.bulk_update(columnsToUpdate, ['name', 'orderNo'])

            if statusesToUpdate:
                ColumnStatus.objects.bulk_update(statusesToUpdate, ['name', 'orderNo'])
        return Response(status=status.HTTP_200_OK)


class TicketColumStatusApiVersion1(APIView):
    def put(self, request, *args, **kwargs):
        columnStatusId = request.data.get('column-status-id')
        ticketIds = request.data.get('ticket-ids')
        tickets = Ticket.objects.filter(id__in=ticketIds)
        for ticket in tickets:
            ticket.columnStatus_id = columnStatusId
            ticket.orderNo = ticketIds.index(str(ticket.id)) + 1
        Ticket.objects.bulk_update(tickets, ['columnStatus', 'orderNo'])
        return Response(status=status.HTTP_200_OK)


class ScrumBoardBacklogTicketUpdateApiVersion1(APIView):
    def put(self, request, *args, **kwargs):
        ticketId = request.data.get('ticket-id')
        zone = request.data.get('zone')
        ticket = Ticket.objects.select_related('columnStatus').get(id=ticketId)
        Sprint.tickets.through.objects.filter(ticket=ticket).delete()

        if zone == 'sprint':
            # remove from other sprints, add it to this sprint, update column status to remove from backlog
            sprint = Sprint.objects.select_related('board').get(id=request.data.get('sprint-id'))
            sprint.tickets.add(ticket)
            ticket.columnStatus = ColumnStatus.objects.filter(
                column__board=sprint.board, column__status=Column.Status.TODO
            ).order_by('id')[:1].first()
            ticket.save()
        elif zone == 'backlog':
            # remove from all sprints, update column status to backlog
            ticket.columnStatus_id = request.data.get('column-id')
            ticket.save()
        return Response(status=status.HTTP_200_OK)


class ScrumBoardBacklogSprintUpdateApiVersion1(APIView):

    def startSprintConditions(self, sprint):
        if not sprint.tickets.exists():
            return 'Selected sprint does not have any tickets. Please add ticket(s) before starting the sprint.'
        if Sprint.objects.filter(board=sprint.board, isActive=True).exclude(id=sprint.id).exists():
            return 'Please complete your existing sprint before starting a new one.'
        if Sprint.objects.filter(board=sprint.board, isComplete=False, id__lt=sprint.id).exclude(id=sprint.id).exists():
            return 'You have an ongoing or incomplete sprint. Please finish it before moving on to the next one.'
        return None

    def put(self, request, *args, **kwargs):
        event = request.data.get('event')
        sprint = Sprint.objects.get(id=request.data.get('sprint-id'))

        if event == 'start-sprint':
            sprintConditions = self.startSprintConditions(sprint)
            if sprintConditions is None:
                sprint.isActive = True
                sprint.save()
            else:
                messages.error(request, sprintConditions)
        elif event == 'complete-sprint':
            with transaction.atomic():
                incompleteTickets = sprint.tickets.filter(
                    columnStatus__column__status__in=[Column.Status.TODO, Column.Status.IN_PROGRESS]
                )
                nextSprint = Sprint.objects.filter(
                    board=sprint.board, isComplete=False, isActive=False
                ).order_by('id').exclude(id=sprint.id).first()

                if nextSprint is None:
                    columnStatus = ColumnStatus.objects.filter(
                        column__board=sprint.board, column__status=Column.Status.BACK_LOG
                    ).order_by('id')[:1].first()
                    incompleteTickets.update(columnStatus=columnStatus)
                else:
                    nextSprint.tickets.add(*incompleteTickets)
                    nextSprint.isActive = True
                    nextSprint.save()

                sprint.tickets.remove(*incompleteTickets)
                sprint.isComplete = True
                sprint.isActive = False
                sprint.save()

        return Response(status=status.HTTP_200_OK)
