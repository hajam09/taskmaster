from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import (
    ColumnStatus,
    Column,
    Ticket
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
