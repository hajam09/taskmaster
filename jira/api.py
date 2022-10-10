import imghdr
import json
import threading
from datetime import datetime
from http import HTTPStatus
import string

from django.contrib import messages
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models import Q
from django.http import QueryDict, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from accounts.models import Team, Component, TeamChatMessage, Profile
from jira.models import Board, Column, Label, Ticket, Project, Sprint, TicketComment, TicketAttachment, ColumnStatus
from taskmaster.operations import databaseOperations, generalOperations


def compare(s1, s2):
    remove = string.punctuation + string.whitespace
    mapping = {ord(c): None for c in remove}
    return s1.translate(mapping) == s2.translate(mapping)


class BoardSettingsViewGeneralDetailsApiEventVersion1Component(View):

    def put(self, *args, **kwargs):
        url = self.kwargs.get("url", None)
        put = QueryDict(self.request.body)

        try:
            board = Board.objects.get(url=url)
        except Board.DoesNotExist:
            response = {
                "success": False,
                "message": "Could not find a board with url/id: {}".format(url)
            }
            return JsonResponse(response, status=HTTPStatus.NOT_FOUND)

        board.internalKey = put.get("board-name", board.internalKey)
        board.isPrivate = put.get("board-visibility") == 'visibility-members'

        board.projects.clear()
        board.admins.clear()
        board.members.clear()

        # just passing the ids will do the job
        board.projects.add(*put.getlist("board-projects[]", []))
        board.admins.add(*put.getlist("board-admins[]", []))
        board.members.add(*put.getlist("board-members[]", []))

        board.save()

        response = {
            "success": True
        }
        return JsonResponse(response, status=HTTPStatus.OK)


@method_decorator(csrf_exempt, name='dispatch')
class BoardSettingsViewBoardColumnsApiEventVersion1Component(View):

    def get(self, *args, **kwargs):
        # NOT_IN_USE
        url = self.kwargs.get("url", None)

        try:
            board = Board.objects.get(url=url)
        except Board.DoesNotExist:
            response = {
                "success": False,
                "message": "Could not find a board with url/id: {}".format(url)
            }
            return JsonResponse(response, status=HTTPStatus.NOT_FOUND)

        def canDeleteOrEdit(columnName):
            return columnName not in ["BACKLOG", "TO DO", "IN PROGRESS", "DONE"]

        response = {
            "success": True,
            "data": {
                "columns": [
                    {
                        "id": column.id,
                        "internalKey": column.internalKey,
                        "canDelete": canDeleteOrEdit(column.internalKey),
                        "canEdit": canDeleteOrEdit(column.internalKey),
                    }
                    for column in board.boardColumns.all()
                ]
            }
        }
        return JsonResponse(response, status=HTTPStatus.OK)

    def post(self, *args, **kwargs):
        # MANUAL_TESTED
        url = self.kwargs.get("url", None)

        try:
            board = Board.objects.get(url=url)
        except Board.DoesNotExist:
            response = {
                "success": False,
                "message": "Could not find a board with url/id: {}".format(url)
            }
            return JsonResponse(response, status=HTTPStatus.NOT_FOUND)

        newColumnName = self.request.POST.get("column-name", None)

        if newColumnName is not None:
            boardColumns = board.boardColumns.all()

            existingColumn = [i for i in boardColumns if i.internalKey.lower() == newColumnName.lower()]
            if len(existingColumn) == 0:
                newColumn = Column.objects.create(
                    board=board,
                    internalKey=newColumnName,
                    orderNo=board.boardColumns.count() + 1
                )
                response = {
                    "success": True,
                    "data": {
                        "id": newColumn.id,
                        "internalKey": newColumn.internalKey,
                        "orderNo": newColumn.orderNo
                    }
                }
                return JsonResponse(response, status=HTTPStatus.OK)
        return JsonResponse({}, status=HTTPStatus.ACCEPTED)

    def put(self, *args, **kwargs):
        # MANUAL_TESTED
        url = self.kwargs.get("url", None)
        put = QueryDict(self.request.body)

        try:
            board = Board.objects.get(url=url)
        except Board.DoesNotExist:
            response = {
                "success": False,
                "message": "Could not find a board with url/id: {}".format(url)
            }
            return JsonResponse(response, status=HTTPStatus.NOT_FOUND)

        columnId = put.get("column-id", None)
        column = databaseOperations.getObjectByIdOrNone(board.boardColumns.all(), columnId)
        if column is None:
            response = {
                "success": False,
                "message": "Could not update the column name."
            }
            return JsonResponse(response, status=HTTPStatus.BAD_REQUEST)

        def canDeleteOrEdit(columnName):
            return columnName not in ["BACKLOG", "TO DO", "IN PROGRESS", "DONE"]

        if not canDeleteOrEdit(column.internalKey):
            response = {
                "success": False,
                "message": "Sorry, you cannot change this column name."
            }
            return JsonResponse(response)

        columnName = put.get("column-name", column.internalKey)
        column.internalKey = columnName
        column.save(update_fields=["internalKey"])

        response = {
            "success": True
        }
        return JsonResponse(response, status=HTTPStatus.OK)

    def delete(self, *args, **kwargs):
        # MANUAL_TESTED
        url = self.kwargs.get("url", None)

        try:
            Board.objects.get(url=url)
        except Board.DoesNotExist:
            response = {
                "success": False,
                "message": "Could not find a board with url/id: {}".format(url)
            }
            return JsonResponse(response, status=HTTPStatus.NOT_FOUND)

        put = QueryDict(self.request.body)
        columnId = put.get("column-id", None)
        column = Column.objects.filter(id=columnId).first()

        def canDeleteOrEdit(columnName):
            return columnName not in ["BACKLOG", "TO DO", "IN PROGRESS", "DONE"]

        if not canDeleteOrEdit(column.internalKey):
            response = {
                "success": False,
                "message": "Sorry, you cannot delete this column."
            }
            return JsonResponse(response)

        if column is not None and column.columnTickets.count() > 0:
            response = {
                "success": False,
                "message": "There's still some tickets in this column."
            }
            return JsonResponse(response)

        column.delete()

        response = {
            "success": True
        }
        return JsonResponse(response, status=HTTPStatus.OK)


@method_decorator(csrf_exempt, name='dispatch')
class TicketBulkOrderChangeApiEventVersion1Component(View):

    def put(self, *args, **kwargs):
        put = QueryDict(self.request.body)
        newOrder = put.getlist('newOrder[]', None)

        ticketList = Ticket.objects.filter(id__in=newOrder[:-1]).order_by('orderNo')
        newOrderList = [databaseOperations.getObjectByIdOrNone(ticketList, i) for i in newOrder[:-1]]

        i = 0
        for j in newOrderList:
            j.orderNo = ticketList[i].orderNo
            i += 1

        Ticket.objects.bulk_update(newOrderList, ['orderNo'])

        response = {
            "success": True
        }
        return JsonResponse(response, status=HTTPStatus.OK)


@method_decorator(csrf_exempt, name='dispatch')
class BoardColumnsBulkOrderChangeApiEventVersion1Component(View):

    def put(self, *args, **kwargs):
        # MANUAL_TESTED
        url = self.kwargs.get("url", None)
        put = QueryDict(self.request.body)

        try:
            board = Board.objects.get(url=url)
        except Board.DoesNotExist:
            response = {
                "success": False,
                "message": "Could not find a board with url/id: {}".format(url)
            }
            return JsonResponse(response, status=HTTPStatus.NOT_FOUND)

        newColumnOrder = put.getlist('new-column-order[]', None)

        if len(newColumnOrder) > 0:
            newColumnOrder = [int(i.split('-')[2]) for i in newColumnOrder]
            for i in board.boardColumns.all():
                i.orderNo = newColumnOrder.index(i.pk)
                i.save(update_fields=['orderNo'])

        response = {
            "success": True
        }
        return JsonResponse(response, status=HTTPStatus.OK)


@method_decorator(csrf_exempt, name='dispatch')
class BoardSettingsViewBoardLabelsApiEventVersion1Component(View):

    def post(self, *args, **kwargs):
        # MANUAL_TESTED
        url = self.kwargs.get("url", None)

        try:
            board = Board.objects.get(url=url)
        except Board.DoesNotExist:
            response = {
                "success": False,
                "message": "Could not find a board with url/id: {}".format(url)
            }
            return JsonResponse(response, status=HTTPStatus.NOT_FOUND)

        newLabelName = self.request.POST.get("label-name", None)

        if newLabelName is None:
            return JsonResponse({}, status=HTTPStatus.ACCEPTED)

        newLabel = Label.objects.create(
            board=board,
            internalKey=newLabelName,
        )
        response = {
            "success": True,
            "data": {
                "id": newLabel.id,
                "internalKey": newLabel.internalKey,
                "colour": newLabel.colour,
                "orderNo": newLabel.orderNo
            }
        }
        return JsonResponse(response, status=HTTPStatus.OK)

    def put(self, *args, **kwargs):
        # MANUAL_TESTED
        url = self.kwargs.get("url", None)
        put = QueryDict(self.request.body)

        try:
            board = Board.objects.get(url=url)
        except Board.DoesNotExist:
            response = {
                "success": False,
                "message": "Could not find a board with url/id: {}".format(url)
            }
            return JsonResponse(response, status=HTTPStatus.NOT_FOUND)

        labelId = put.get("label-id", None)
        label = databaseOperations.getObjectByIdOrNone(board.boardLabels.all(), labelId)
        if label is None:
            response = {
                "success": False,
                "message": "Could not update the label name."
            }
            return JsonResponse(response, status=HTTPStatus.BAD_REQUEST)

        labelName = put.get("label-name", label.internalKey)
        labelColour = put.get("label-colour", label.colour)

        updateFields = ['internalKey', 'colour']
        label.internalKey = labelName
        label.colour = labelColour
        label.save(update_fields=updateFields)

        response = {
            "success": True
        }
        return JsonResponse(response, status=HTTPStatus.OK)

    def delete(self, *args, **kwargs):
        # MANUAL_TESTED
        url = self.kwargs.get("url", None)

        try:
            board = Board.objects.get(url=url)
        except Board.DoesNotExist:
            response = {
                "success": False,
                "message": "Could not find a board with url/id: {}".format(url)
            }
            return JsonResponse(response, status=HTTPStatus.NOT_FOUND)

        put = QueryDict(self.request.body)
        labelId = put.get("label-id", None)

        Label.objects.filter(id=labelId, board=board).update(deleteFl=True)

        response = {
            "success": True
        }
        return JsonResponse(response, status=HTTPStatus.OK)


@method_decorator(csrf_exempt, name='dispatch')
class TeamsViewApiEventVersion1Component(View):
    def put(self, *args, **kwargs):
        teamId = self.kwargs.get("teamId", None)

        try:
            thisTeam = Team.objects.get(id=teamId)
        except Team.DoesNotExist:
            response = {
                "success": False,
                "message": "Could not find a team with url/id: {}".format(teamId)
            }
            return JsonResponse(response, status=HTTPStatus.NOT_FOUND)

        thisTeam.members.remove(self.request.user)
        thisTeam.admins.remove(self.request.user)

        response = {
            "success": True
        }
        return JsonResponse(response, status=HTTPStatus.OK)


class TeamsObjectApiEventVersion1Component(View):
    # TeamsObjectApiEventVersion1ComponentTest

    def delete(self, *args, **kwargs):
        # MANUAL_TESTED
        teamId = self.kwargs.get("teamId", None)

        try:
            thisTeam = Team.objects.get(id=teamId)
        except Team.DoesNotExist:
            response = {
                "success": False,
                "message": "Could not find a team with url/id: {}".format(teamId)
            }
            return JsonResponse(response, status=HTTPStatus.NOT_FOUND)

        if self.request.user in thisTeam.admins.all():
            thisTeam.deleteFl = True
            thisTeam.save(update_fields=['deleteFl'])
            messages.success(
                self.request,
                'Your team has been deleted successfully!'
            )
            response = {
                "success": True
            }
        else:
            response = {
                "success": False,
                "message": "You don't have the permission to complete this operation."
            }
        return JsonResponse(response, status=HTTPStatus.OK)


@method_decorator(csrf_exempt, name='dispatch')
class TicketCommentObjectApiEventVersion1Component(View):

    def post(self, *args, **kwargs):
        body = json.loads(self.request.body.decode())
        ticketId = body.get("ticketId")
        comment = body.get("comment")

        if not self.request.user.is_authenticated:
            response = {
                "success": False,
                "message": "Please login to add a comment"
            }
            return JsonResponse(response, status=HTTPStatus.UNAUTHORIZED)

        try:
            ticket = Ticket.objects.get(id=ticketId)
        except Ticket.DoesNotExist:
            response = {
                "success": False,
                "message": "Could not find a ticket with id: {}".format(ticketId)
            }
            return JsonResponse(response, status=HTTPStatus.NOT_FOUND)

        newCommentNumber = TicketComment.objects.count()

        ticketComment = TicketComment()
        ticketComment.ticket = ticket
        ticketComment.creator = self.request.user
        ticketComment.comment = comment
        ticketComment.orderNo = newCommentNumber + 1
        ticketComment.save()

        data = {
            'id': ticketComment.pk,
            'comment': ticketComment.comment,
            'edited': ticketComment.edited,
            'likes': {
                'count': 0,
                'liked': False
            },
            'dislikes': {
                'count': 0,
                'liked': False
            },
            'creator': generalOperations.serializeUserVersion2(ticketComment.creator),
        }

        response = {
            'success': True,
            'data': data
        }
        return JsonResponse(response, status=HTTPStatus.OK)

    def delete(self, *args, **kwargs):
        body = json.loads(self.request.body)
        TicketComment.objects.filter(id=body['id']).delete()
        response = {
            'success': True,
        }
        return JsonResponse(response, status=HTTPStatus.OK)

    def put(self, *args, **kwargs):
        body = json.loads(self.request.body)
        TicketComment.objects.filter(id=body['id']).update(comment=body['comment'], edited=True)
        response = {
            'success': True,
        }
        return JsonResponse(response, status=HTTPStatus.OK)


@method_decorator(csrf_exempt, name='dispatch')
class TicketObjectForEpicTicketApiEventVersion1Component(View):

    def post(self, *args, **kwargs):
        body = json.loads(self.request.body.decode())
        epicTicketId = body.get("ticketId")
        summary = body.get("ticketSummary")
        issueType = body.get("issueType")

        try:
            epicTicket = Ticket.objects.get(id=epicTicketId)
        except Ticket.DoesNotExist:
            response = {
                "success": False,
                "message": "Could not find a ticket with id: {}".format(epicTicketId)
            }
            return JsonResponse(response, status=HTTPStatus.NOT_FOUND)

        newTicketNumber = epicTicket.project.projectTickets.count() + 1

        ticket = Ticket()
        ticket.internalKey = epicTicket.project.code + "-" + str(newTicketNumber)
        ticket.summary = summary
        ticket.resolution = Component.objects.get(componentGroup__code='TICKET_RESOLUTIONS', code="UNRESOLVED")
        ticket.project = epicTicket.project
        ticket.reporter = self.request.user
        ticket.issueType = Component.objects.get(componentGroup__code='TICKET_ISSUE_TYPE', internalKey=issueType)
        ticket.priority = Component.objects.get(componentGroup__code='TICKET_PRIORITY', code="MEDIUM")
        ticket.board = epicTicket.board
        ticket.column = Column.objects.get(board=epicTicket.board, internalKey='TO DO')
        ticket.epic = epicTicket
        ticket.orderNo = newTicketNumber
        ticket.save()

        # TODO: Update to the current sprint

        data = {
            'id': ticket.pk,
            'internalKey': ticket.internalKey,
            'summary': ticket.summary,
            'url': ticket.getTicketUrl(),
            'issueType': {
                'id': ticket.issueType.pk,
                'icon': ticket.issueType.icon,
                'internalKey': ticket.issueType.internalKey
            },
            'priority': {
                'id': ticket.priority.pk,
                'icon': ticket.priority.icon,
                'internalKey': ticket.priority.internalKey
            }
        }

        response = {
            'success': True,
            'data': data
        }
        return JsonResponse(response, status=HTTPStatus.OK)


class TicketCommentsApiEventVersion1Component(View):
    def get(self, *args, **kwargs):
        ticketId = self.kwargs.get("ticketId", None)

        ticketComments = TicketComment.objects.filter(ticket__id=ticketId).select_related(
            'creator__profile').prefetch_related('likes', 'dislikes')

        comments = [
            {
                'id': comment.id,
                'comment': comment.comment,
                'edited': comment.edited,
                'createdDttm': datetime.strftime(comment.createdDttm, '%d %B %Y, %I:%M %p'),
                'likes': {
                    'count': comment.likes.count(),
                    'liked': self.request in comment.likes.all()
                },
                'dislikes': {
                    'count': comment.dislikes.count(),
                    'disliked': self.request in comment.dislikes.all()
                },
                'creator': generalOperations.serializeUserVersion2(comment.creator),
                'canEdit': comment.creator.id == self.request.user.id,
            }
            for comment in ticketComments
        ]

        response = {
            "success": True,
            "data": {
                "comments": comments
            }
        }
        return JsonResponse(response, status=HTTPStatus.OK)


@method_decorator(csrf_exempt, name='dispatch')
class TicketAttachmentsApiEventVersion1Component(View):

    def get(self, *args, **kwargs):
        ticketId = self.kwargs.get("ticketId", None)

        ticketAttachments = TicketAttachment.objects.filter(ticket__id=ticketId)
        fileIcons = cache.get('FILE_ICONS')
        unknownFileType = databaseOperations.getObjectByInternalKey(fileIcons, 'unknown')

        def getIcon(i):
            extension = imghdr.what(i.attachment)
            isImage = extension is not None

            if isImage:
                return i.attachment.url

            otherFileType = databaseOperations.getObjectByInternalKey(fileIcons, i.attachment.name.split('.')[-1])
            if otherFileType is not None:
                return otherFileType.icon
            return unknownFileType.icon

        attachments = [
            {
                'id': i.id,
                'url': i.attachment.url,
                'icon': getIcon(i),
                'internalKey': i.internalKey,
                'canDelete': i.uploadedBy.id == self.request.user.id,
                'name': i.attachment.name.split("/")[1],
                'size': f'{ticketAttachments.first().attachment.size} bytes',
                'createdDttm': i.createdDttm.strftime('%Y-%m-%d %H:%M')
            }
            for i in ticketAttachments
        ]

        response = {
            "success": True,
            "data": {
                "attachments": attachments
            }
        }
        return JsonResponse(response, status=HTTPStatus.OK)


@method_decorator(csrf_exempt, name='dispatch')
class TicketsForEpicTicketApiEventVersion1Component(View):

    def get(self, *args, **kwargs):
        ticketId = self.kwargs.get("ticketId", None)

        try:
            ticket = Ticket.objects.select_related('priority', 'issueType', 'assignee__profile').get(id=ticketId)
        except Ticket.DoesNotExist:
            response = {
                "success": False,
                "message": "Could not find a ticket with id: {}".format(ticketId)
            }
            return JsonResponse(response, status=HTTPStatus.NOT_FOUND)

        epicTickets = [
            {
                'id': i.pk,
                'internalKey': i.internalKey,
                'summary': i.summary,
                'url': i.getTicketUrl(),
                'assignee': {
                    'id': i.assignee.pk,
                    'fullName': i.assignee.get_full_name(),
                    'icon': i.assignee.profile.profilePicture.url
                } if i.assignee is not None else {},
                'issueType': {
                    'id': i.issueType.pk,
                    'icon': i.issueType.icon,
                    'internalKey': i.issueType.internalKey
                },
                'priority': {
                    'id': i.priority.pk,
                    'icon': i.priority.icon,
                    'internalKey': i.priority.internalKey
                }
            }
            for i in ticket.epicTickets.all()
        ]

        response = {
            "success": True,
            "data": {
                "tickets": epicTickets
            }
        }
        return JsonResponse(response, status=HTTPStatus.OK)


class TicketObjectApiEventVersion1Component(View):

    def put(self, *args, **kwargs):
        ticketId = self.kwargs.get("ticketId", None)

        try:
            ticket = Ticket.objects.select_related('columnStatus').get(id=ticketId)
        except Ticket.DoesNotExist:
            response = {
                "success": False,
                "message": "Could not find a ticket with id: {}".format(ticketId)
            }
            return JsonResponse(response, status=HTTPStatus.NOT_FOUND)

        body = json.loads(self.request.body.decode())
        for key, value in body.items():
            setattr(ticket, f"{key}_id", int(value))

        resolutionList = cache.get('TICKET_RESOLUTIONS')
        resolvedResolution = databaseOperations.getObjectByCode(resolutionList, "RESOLVED")
        reOpenedResolution = databaseOperations.getObjectByCode(resolutionList, "REOPENED")
        unResolvedResolution = databaseOperations.getObjectByCode(resolutionList, "UNRESOLVED")

        if ticket.columnStatus.category == ColumnStatus.Category.DONE:
            ticket.resolution_id = resolvedResolution.id
        else:
            if ticket.resolution == resolvedResolution:
                ticket.resolution_id = reOpenedResolution.id
            elif ticket.resolution == reOpenedResolution:
                ticket.resolution_id = unResolvedResolution.id

        ticket.save()
        response = {
            "success": True,
        }
        return JsonResponse(response, status=HTTPStatus.OK)


@method_decorator(csrf_exempt, name='dispatch')
class SubTaskTicketObjectForTicketApiEventVersion1Component(View):

    def post(self, *args, **kwargs):
        body = json.loads(self.request.body.decode())
        parentTicketId = body.get("ticketId")
        summary = body.get("ticketSummary")

        try:
            parentTicket = Ticket.objects.get(id=parentTicketId)
        except Ticket.DoesNotExist:
            response = {
                "success": False,
                "message": "Could not find a ticket with id: {}".format(parentTicketId)
            }
            return JsonResponse(response, status=HTTPStatus.NOT_FOUND)

        newTicketNumber = parentTicket.project.projectTickets.count() + 1

        ticket = Ticket()
        ticket.internalKey = parentTicket.project.code + "-" + str(newTicketNumber)
        ticket.summary = summary
        ticket.resolution_id = next((i.id for i in cache.get('TICKET_RESOLUTIONS') if i.code == 'UNRESOLVED'))
        ticket.project_id = parentTicket.project_id
        ticket.reporter_id = self.request.user.id
        ticket.issueType_id = next((i.id for i in cache.get('TICKET_ISSUE_TYPE') if i.code == 'SUB_TASK'))
        ticket.priority_id = next((i.id for i in cache.get('TICKET_PRIORITY') if i.code == 'MEDIUM'))
        ticket.columnStatus_id = parentTicket.columnStatus_id
        ticket.orderNo = newTicketNumber
        ticket.save()

        parentTicket.subTask.add(ticket)

        response = {
            'success': True,
        }
        return JsonResponse(response, status=HTTPStatus.OK)


@method_decorator(csrf_exempt, name='dispatch')
class SubTaskTicketsForTicketApiEventVersion1Component(View):

    def get(self, *args, **kwargs):
        ticketId = self.kwargs.get("ticketId", None)

        try:
            ticket = Ticket.objects.select_related('priority', 'issueType', 'assignee__profile').get(id=ticketId)
        except Ticket.DoesNotExist:
            response = {
                "success": False,
                "message": "Could not find a ticket with id: {}".format(ticketId)
            }
            return JsonResponse(response, status=HTTPStatus.NOT_FOUND)

        subTasks = [
            {
                'id': i.pk,
                'internalKey': i.internalKey,
                'summary': i.summary,
                'url': i.getTicketUrl(),
                'assignee': {
                    'id': i.assignee.pk,
                    'fullName': i.assignee.get_full_name(),
                    'icon': i.assignee.profile.profilePicture.url
                } if i.assignee is not None else {},
                'issueType': {
                    'id': i.issueType.pk,
                    'icon': i.issueType.icon,
                    'internalKey': i.issueType.internalKey
                },
                'priority': {
                    'id': i.priority.pk,
                    'icon': i.priority.icon,
                    'internalKey': i.priority.internalKey
                }
            }
            for i in ticket.subTask.all().order_by('orderNo')
        ]

        response = {
            "success": True,
            "data": {
                "tickets": subTasks
            }
        }
        return JsonResponse(response, status=HTTPStatus.OK)


@method_decorator(csrf_exempt, name='dispatch')
class AgileBoardTicketColumnUpdateApiEventVersion1Component(View):

    def put(self, *args, **kwargs):
        put = QueryDict(self.request.body)

        columnId = put.get("columnId")
        ticketId = put.get("ticketId")

        column = Column.objects.get(id=columnId)
        ticket = Ticket.objects.select_related('column').get(id=ticketId)

        if column.internalKey == "DONE":
            ticket.resolution = Component.objects.get(componentGroup__code="TICKET_RESOLUTIONS", code="RESOLVED")
        else:
            if ticket.column.internalKey == "DONE" and column.internalKey != "BACKLOG":
                ticket.resolution = Component.objects.get(componentGroup__code="TICKET_RESOLUTIONS", code="REOPENED")

        ticket.column = column
        ticket.save()

        response = {
            "success": True,
        }
        return JsonResponse(response, status=HTTPStatus.OK)


class AgileBoardTicketColumnUpdateApiEventVersion2Component(View):

    def put(self, *args, **kwargs):
        put = QueryDict(self.request.body)

        columnId = put.get("columnId")
        ticketId = put.get("ticketId")

        ticket = Ticket.objects.select_related("resolution__componentGroup").get(id=ticketId)
        column = Column.objects.get(id=columnId)
        columnStatus = ColumnStatus.objects.filter(column_id=column).first()

        resolvedComponent = Component.objects.get(componentGroup__code="TICKET_RESOLUTIONS", code="RESOLVED")
        if columnStatus.setResolution:
            ticket.resolution = resolvedComponent
        elif ticket.resolution == resolvedComponent:
            ticket.resolution = Component.objects.get(componentGroup__code="TICKET_RESOLUTIONS", code="REOPENED")

        ticket.columnStatus = columnStatus
        ticket.save()

        response = {
            "success": True,
        }
        return JsonResponse(response, status=HTTPStatus.OK)


@method_decorator(csrf_exempt, name='dispatch')
class AgileBoardDetailsApiEventVersion1Component(View):

    def get(self, *args, **kwargs):
        boardId = self.kwargs.get("boardId", None)

        try:
            board = Board.objects.get(id=boardId)
        except Board.DoesNotExist:
            response = {
                "success": False,
                "message": "Could not find a board for id: " + str(boardId)
            }
            return JsonResponse(response, status=HTTPStatus.NOT_FOUND)

        columnsList = []
        if board.type == Board.Types.SCRUM:
            currentSprint = Sprint.objects.filter(board__id=boardId, isComplete=False).order_by('orderNo').first()
            columns = Column.objects.filter(Q(board_id=board.id), ~Q(internalKey="BACKLOG"))
            if currentSprint is not None:
                sprintTickets = currentSprint.tickets.filter(~Q(issueType__code="EPIC")).select_related(
                    'assignee__profile',
                    'column',
                    'epic', 'issueType',
                    'priority',
                    'resolution')

                for column in columns:
                    allColumnTickets = [i for i in sprintTickets if i.column == column]
                    tickets = []
                    serializeTickets(allColumnTickets, tickets, False)
                    data = {
                        "id": column.id,
                        "internalKey": column.internalKey,
                        "tickets": tickets
                    }
                    columnsList.append(data)
        else:
            columns = Column.objects.filter(Q(board_id=board.id), ~Q(internalKey="BACKLOG")).prefetch_related(
                'columnTickets')

            for column in columns:
                allColumnTickets = column.columnTickets.filter(~Q(issueType__code="EPIC")).select_related(
                    'assignee__profile',
                    'column', 'epic',
                    'issueType',
                    'priority',
                    'resolution')

                tickets = []
                serializeTickets(allColumnTickets, tickets, False)
                data = {
                    "id": column.id,
                    "internalKey": column.internalKey,
                    "tickets": tickets
                }
                columnsList.append(data)

        response = {
            "success": True,
            "data": {
                "columns": columnsList
            }
        }
        # TODO: Add board details, members of the board, and sprint details...
        return JsonResponse(response, status=HTTPStatus.OK)


@method_decorator(csrf_exempt, name='dispatch')
class AgileBoardDetailsApiEventVersion2Component(View):

    def get(self, *args, **kwargs):
        boardId = self.kwargs.get("boardId", None)

        try:
            board = Board.objects.get(id=boardId)
        except Board.DoesNotExist:
            response = {
                "success": False,
                "message": "Could not find a board for id: " + str(boardId)
            }
            return JsonResponse(response, status=HTTPStatus.NOT_FOUND)

        columnsList = []

        if board.type == Board.Types.SCRUM:
            currentSprint = Sprint.objects.filter(board__id=boardId, isComplete=False).order_by('orderNo').first()
            boardColumns = Column.objects.filter(Q(board_id=boardId), ~Q(internalKey="BACKLOG"))
            columnStatusList = ColumnStatus.objects.filter(
                Q(board_id=boardId), ~Q(column=None)
            ).select_related('column')

            if currentSprint is not None:
                sprintTickets = currentSprint.tickets.filter(
                    ~Q(issueType__code="EPIC")
                ).select_related("issueType", "columnStatus", "assignee__profile", "epic", "priority", "resolution")

                for column in boardColumns:
                    tickets = []
                    columnStatuses = [i for i in columnStatusList if i.column == column]
                    columnTickets = [t for t in sprintTickets if t.columnStatus in columnStatuses]
                    serializeTickets(columnTickets, tickets, False)

                    data = {
                        "id": column.id,
                        "internalKey": column.internalKey,
                        "tickets": tickets
                    }
                    columnsList.append(data)

        else:
            boardColumns = Column.objects.filter(Q(board_id=boardId), ~Q(internalKey="BACKLOG"))
            columnStatusList = ColumnStatus.objects.filter(Q(board_id=boardId), ~Q(column=None)).select_related('column')
            allTickets = Ticket.objects.filter(
                Q(columnStatus__in=columnStatusList), ~Q(issueType__code="EPIC")
            ).select_related("issueType", "columnStatus", "assignee__profile", "epic", "priority", "resolution")

            today = datetime.now().date()

            for column in boardColumns:
                tickets = []
                columnStatuses = [i for i in columnStatusList if i.column == column]
                columnTickets = [t for t in allTickets if t.columnStatus in columnStatuses]

                # For KANBAN BOARD remove two weeks old Done Tickets.
                if column.category == Column.Category.DONE:
                    columnTickets = [
                        ticket for ticket in columnTickets
                        if (today - datetime.strptime(str(ticket.modifiedDttm.date()), '%Y-%m-%d').date()).days <= 14
                    ]

                serializeTickets(columnTickets, tickets, False)

                data = {
                    "id": column.id,
                    "internalKey": column.internalKey,
                    "tickets": tickets
                }
                columnsList.append(data)

        response = {
            "success": True,
            "data": {
                "columns": columnsList
            }
        }
        return JsonResponse(response, status=HTTPStatus.OK)


@method_decorator(csrf_exempt, name='dispatch')
class BacklogDetailsEpicLessTicketsApiEventVersion1Component(View):

    def get(self, *args, **kwargs):
        boardId = self.kwargs.get("boardId", None)

        try:
            board = Board.objects.prefetch_related('boardSprints').get(id=boardId)
        except Board.DoesNotExist:
            response = {
                "success": False,
                "message": "Could not find a board for id: " + str(boardId)
            }
            return JsonResponse(response, status=HTTPStatus.NOT_FOUND)

        backlogGroups = []
        if board.type == Board.Types.SCRUM:
            openSprints = Sprint.objects.filter(board__id=boardId, isComplete=False).order_by('orderNo')
            for sprint in openSprints:
                serializedTickets = []
                sprintTickets = sprint.tickets.filter(~Q(issueType__code="EPIC"), epic=None).select_related(
                    'assignee__profile',
                    'column',
                    'epic', 'issueType',
                    'priority',
                    'resolution')

                serializeTickets(sprintTickets, serializedTickets, False)
                sprintData = {
                    'id': sprint.id,
                    'internalKey': sprint.internalKey,
                    'isActive': openSprints[0].id == sprint.id,
                    'tickets': serializedTickets,
                }
                backlogGroups.append(sprintData)

            # Get backlog group and its tickets.
            backlogTickets = Ticket.objects.filter(
                ~Q(issueType__code="EPIC"), board__id=boardId, column__internalKey="BACKLOG", epic=None
            ).select_related(
                'assignee__profile',
                'column',
                'epic', 'issueType',
                'priority',
                'resolution')

            serializedTickets = []
            serializeTickets(backlogTickets, serializedTickets, False)
            backlogGroups.append(
                {
                    'id': 0,
                    'internalKey': 'Backlog',
                    'isActive': False,
                    'tickets': serializedTickets,
                }
            )

        else:
            boardTickets = Ticket.objects.filter(
                ~Q(issueType__code="EPIC"), epic=None, column__board__id=boardId).select_related(
                'assignee__profile',
                'column',
                'epic', 'issueType',
                'priority',
                'resolution')

            developmentTickets = [i for i in boardTickets if i.column.internalKey != "BACKLOG"]
            backlogTickets = [i for i in boardTickets if i.column.internalKey == "BACKLOG"]

            emptyDevelopmentTickets = []
            emptyBacklogTickets = []

            serializeTickets(developmentTickets, emptyDevelopmentTickets, False)
            serializeTickets(backlogTickets, emptyBacklogTickets, False)

            backlogGroups.append(
                {
                    "id": 1,
                    "internalKey": "In development",
                    "isActive": True,
                    "tickets": emptyDevelopmentTickets
                }
            )
            backlogGroups.append(
                {
                    "id": 0,
                    "internalKey": "Backlog",
                    "isActive": False,
                    "tickets": emptyBacklogTickets
                }
            )
        response = {
            "success": True,
            "data": {
                "backlogGroups": backlogGroups,
            }
        }
        return JsonResponse(response, status=HTTPStatus.OK)


class BacklogDetailsApiEventVersion1Component(View):

    def get(self, *args, **kwargs):
        boardId = self.kwargs.get("boardId", None)

        try:
            board = Board.objects.prefetch_related('boardSprints').get(id=boardId)
        except Board.DoesNotExist:
            response = {
                "success": False,
                "message": "Could not find a board for id: " + str(boardId)
            }
            return JsonResponse(response, status=HTTPStatus.NOT_FOUND)

        backlogGroups = []
        if board.type == Board.Types.SCRUM:
            openSprints = Sprint.objects.filter(board__id=boardId, isComplete=False).order_by('orderNo')
            for sprint in openSprints:
                serializedTickets = []
                sprintTickets = sprint.tickets.filter(~Q(issueType__code="EPIC")).select_related('assignee__profile',
                                                                                                 'column',
                                                                                                 'epic', 'issueType',
                                                                                                 'priority',
                                                                                                 'resolution')
                serializeTickets(sprintTickets, serializedTickets, False)
                sprintData = {
                    'id': sprint.id,
                    'internalKey': sprint.internalKey,
                    'isActive': openSprints[0].id == sprint.id,
                    'tickets': serializedTickets,
                }
                backlogGroups.append(sprintData)

            # Get backlog group and its tickets.
            backlogTickets = Ticket.objects.filter(
                ~Q(issueType__code="EPIC"), board__id=boardId, column__internalKey="BACKLOG"
            ).select_related(
                'assignee__profile',
                'column',
                'epic', 'issueType',
                'priority',
                'resolution')

            serializedTickets = []
            serializeTickets(backlogTickets, serializedTickets, False)
            backlogGroups.append(
                {
                    'id': 0,
                    'internalKey': 'Backlog',
                    'isActive': False,
                    'tickets': serializedTickets,
                }
            )

        else:
            boardTickets = Ticket.objects.filter(~Q(issueType__code="EPIC"), column__board__id=boardId).select_related(
                'assignee__profile',
                'column',
                'epic', 'issueType',
                'priority',
                'resolution')

            developmentTickets = [i for i in boardTickets if i.column.internalKey != "BACKLOG"]
            backlogTickets = [i for i in boardTickets if i.column.internalKey == "BACKLOG"]

            emptyDevelopmentTickets = []
            emptyBacklogTickets = []

            serializeTickets(developmentTickets, emptyDevelopmentTickets, False)
            serializeTickets(backlogTickets, emptyBacklogTickets, False)

            backlogGroups.append(
                {
                    "id": 1,
                    "internalKey": "In development",
                    "isActive": True,
                    "tickets": emptyDevelopmentTickets
                }
            )
            backlogGroups.append(
                {
                    "id": 0,
                    "internalKey": "Backlog",
                    "isActive": False,
                    "tickets": emptyBacklogTickets
                }
            )

        response = {
            "success": True,
            "data": {
                "backlogGroups": backlogGroups,
            }
        }
        return JsonResponse(response, status=HTTPStatus.OK)

    def put(self, *args, **kwargs):
        boardId = self.kwargs.get("boardId", None)

        try:
            board = Board.objects.prefetch_related('boardColumns').get(id=boardId)
        except Board.DoesNotExist:
            response = {
                "success": False,
                "message": "Could not find a board for id: " + str(boardId)
            }
            return JsonResponse(response, status=HTTPStatus.NOT_FOUND)

        put = QueryDict(self.request.body)
        columnId = put.get('columnId')
        ticketIds = put.getlist('ticketIds[]')

        ticketList = Ticket.objects.filter(id__in=ticketIds)
        backLogColumn = databaseOperations.getObjectByInternalKey(board.boardColumns.all(), 'BACKLOG')
        toDoColumn = databaseOperations.getObjectByInternalKey(board.boardColumns.all(), 'TO DO')

        if board.type == Board.Types.SCRUM:
            openSprints = Sprint.objects.filter(board__id=boardId, isComplete=False)

            if columnId == '0':
                # Tickets are moved to backlog from sprint plan.
                # Set Tickets column to this boards backlog.
                # Remove tickets from every other sprints.
                ticketList.update(column_id=backLogColumn.id, board_id=board.id)
                for sprint in openSprints:
                    sprint.removeTicketsFromSprint(ticketIds)

            else:
                # Tickets are moved to sprint planning from other sprints or backlog.
                # Set Tickets column to this boards OPEN if newly dragged.
                # Remove tickets from every other sprints.
                # Add Tickets to this sprint.
                # If tickets already in this sprint, then don't change its column.
                draggedToSprint = databaseOperations.getObjectByIdOrNone(openSprints, columnId)
                ticketList.filter(column__internalKey='BACKLOG').update(column_id=toDoColumn.id, board_id=board.id)

                draggedTicket = list(set(ticketList)-set(draggedToSprint.tickets.all()))
                if len(draggedTicket) > 0:
                    draggedTicket[0].board_id = board.id
                    draggedTicket[0].column_id = toDoColumn.id
                    draggedTicket[0].save()

                for sprint in openSprints:
                    if sprint == draggedToSprint:
                        sprint.addTicketsToSprint(ticketIds)
                    else:
                        sprint.removeTicketsFromSprint(ticketIds)
        else:
            if columnId == '0':
                # Ticket is sent to Backlog
                ticketList.update(column_id=backLogColumn.id, board_id=board.id)
            else:
                # Ticket is sent to In development
                ticketList.filter(column__internalKey='BACKLOG').update(column_id=toDoColumn.id, board_id=board.id)

        response = {
            "success": True,
        }
        return JsonResponse(response, status=HTTPStatus.OK)


class BacklogDetailsApiEventVersion2Component(View):

    def get(self, *args, **kwargs):
        boardId = self.kwargs.get("boardId", None)

        try:
            board = Board.objects.prefetch_related('boardSprints').get(id=boardId)
        except Board.DoesNotExist:
            response = {
                "success": False,
                "message": "Could not find a board for id: " + str(boardId)
            }
            return JsonResponse(response, status=HTTPStatus.NOT_FOUND)

        backlogGroups = []
        if board.type == Board.Types.SCRUM:
            openSprints = Sprint.objects.filter(board__id=boardId, isComplete=False).order_by('orderNo')
            for sprint in openSprints:
                serializedTickets = []
                sprintTickets = sprint.tickets.filter(~Q(issueType__code="EPIC")).select_related('assignee__profile',
                                                                                                 'column',
                                                                                                 'epic', 'issueType',
                                                                                                 'priority',
                                                                                                 'resolution')
                serializeTickets(sprintTickets, serializedTickets, False)
                sprintData = {
                    'id': sprint.id,
                    'internalKey': sprint.internalKey,
                    'isActive': openSprints[0].id == sprint.id,
                    'tickets': serializedTickets,
                }
                backlogGroups.append(sprintData)

            # Get backlog group and its tickets.
            backlogTickets = Ticket.objects.filter(
                ~Q(issueType__code="EPIC"), columnStatus__board__id=boardId, columnStatus__internalKey="OPEN"
            ).select_related(
                'assignee__profile',
                'column',
                'epic', 'issueType',
                'priority',
                'resolution')

            serializedTickets = []
            serializeTickets(backlogTickets, serializedTickets, False)
            backlogGroups.append(
                {
                    'id': 0,
                    'internalKey': 'Backlog',
                    'isActive': False,
                    'tickets': serializedTickets,
                }
            )
        else:
            boardTickets = Ticket.objects.filter(~Q(issueType__code="EPIC"), columnStatus__board__id=boardId).select_related(
                'assignee__profile',
                'column',
                'epic', 'issueType',
                'priority',
                'resolution')

            """
            Remove old tickets from DONE column
            show: Not done tickets
            show: Done tickets and modifiedDttm <= 14
            """
            today = datetime.now().date()
            boardTickets = [
                i for i in boardTickets
                if i.columnStatus.category != ColumnStatus.Category.DONE or (i.columnStatus.category == ColumnStatus.Category.DONE and (today - datetime.strptime(str(i.modifiedDttm.date()), '%Y-%m-%d').date()).days <= 14)
            ]

            developmentTickets = [i for i in boardTickets if i.columnStatus.internalKey != "OPEN"]
            backlogTickets = [i for i in boardTickets if i.columnStatus.internalKey == "OPEN"]

            emptyDevelopmentTickets = []
            emptyBacklogTickets = []

            serializeTickets(developmentTickets, emptyDevelopmentTickets, False)
            serializeTickets(backlogTickets, emptyBacklogTickets, False)

            backlogGroups.append(
                {
                    "id": 1,
                    "internalKey": "In development",
                    "isActive": True,
                    "tickets": emptyDevelopmentTickets
                }
            )
            backlogGroups.append(
                {
                    "id": 0,
                    "internalKey": "Backlog",
                    "isActive": False,
                    "tickets": emptyBacklogTickets
                }
            )

        response = {
            "success": True,
            "data": {
                "backlogGroups": backlogGroups,
            }
        }
        return JsonResponse(response, status=HTTPStatus.OK)

    def put(self, *args, **kwargs):
        boardId = self.kwargs.get("boardId", None)

        try:
            board = Board.objects.prefetch_related('boardColumns').get(id=boardId)
        except Board.DoesNotExist:
            response = {
                "success": False,
                "message": "Could not find a board for id: " + str(boardId)
            }
            return JsonResponse(response, status=HTTPStatus.NOT_FOUND)

        put = QueryDict(self.request.body)
        columnId = put.get('columnId')
        ticketIds = put.getlist('ticketIds[]')
        ticketList = Ticket.objects.filter(id__in=ticketIds)
        toDoColumn = ColumnStatus.objects.get(internalKey="TO DO", board_id=board.id, column__internalKey="TO DO")
        backLogColumn = ColumnStatus.objects.get(internalKey="OPEN", board_id=board.id, column__internalKey="BACKLOG")

        if board.type == Board.Types.SCRUM:
            openSprints = Sprint.objects.filter(board__id=boardId, isComplete=False)

            if columnId == '0':
                # Tickets are sent to backlog.
                # Remove from all the sprints.
                # Set the column to backlog
                ticketList.update(columnStatus=backLogColumn)
                for sprint in openSprints:
                    sprint.removeTicketsFromSprint(ticketIds)

            else:
                # Tickets are moved to sprint planning from other sprints or backlog.
                # Add all the tickets to this sprint, but remove from other sprints.
                # Set the new ticket column to TO DO column.
                draggedToSprint = databaseOperations.getObjectByIdOrNone(openSprints, columnId)
                draggedTickets = list(set(ticketList)-set(draggedToSprint.tickets.all()))

                for i in draggedTickets:
                    i.columnStatus = toDoColumn

                Ticket.objects.bulk_update(draggedTickets, ['columnStatus'])

                for sprint in openSprints:
                    if sprint == draggedToSprint:
                        sprint.addTicketsToSprint(ticketIds)
                    else:
                        sprint.removeTicketsFromSprint(ticketIds)

        else:
            if columnId == '0':
                # Ticket is sent to Backlog
                ticketList.update(columnStatus=backLogColumn)
            else:
                # Ticket is sent to In development
                ticketList.filter(
                    columnStatus__internalKey='OPEN', columnStatus__board_id=boardId
                ).update(columnStatus=toDoColumn)

        response = {
            "success": True,
        }
        return JsonResponse(response, status=HTTPStatus.OK)


@method_decorator(csrf_exempt, name='dispatch')
class EpicDetailsForBoardApiEventVersion1Component(View):
    def get(self, *args, **kwargs):
        boardId = self.kwargs.get("boardId", None)

        try:
            board = Board.objects.prefetch_related('projects').get(id=boardId)
        except Board.DoesNotExist:
            response = {
                "success": False,
                "message": "Could not find a board for id: " + str(boardId)
            }
            return JsonResponse(response, status=HTTPStatus.NOT_FOUND)

        def epicTicketStats(childTickets):
            notStarted = 0  # number of pending tickets in this epic
            inProgress = 0  # number of in progress tickets in this epic
            issues = 0  # number of tickets in this epic
            completed = 0  # number of completed tickets in this epic
            unEstimated = 0  # number of tickets with no story points
            estimated = 0  # total number of estimated story points

            for childTicket in childTickets:
                issues += 1

                if childTicket.columnStatus is None:
                    notStarted += 1
                else:
                    if childTicket.columnStatus.category == ColumnStatus.Category.TODO:
                        notStarted += 1
                    elif childTicket.columnStatus.category == ColumnStatus.Category.IN_PROGRESS:
                        inProgress += 1
                    elif childTicket.columnStatus.category == ColumnStatus.Category.DONE:
                        completed += 1
                    else:
                        raise Exception("Unexpected columnStatus.category for ticket ", childTicket.id)

                if childTicket.storyPoints is None:
                    unEstimated += 1
                else:
                    estimated += childTicket.storyPoints

            data = {
                "notStarted": notStarted,
                "inProgress": inProgress,
                "issues": issues,
                "completed": completed,
                "unEstimated": unEstimated,
                "estimated": estimated,
            }
            return data

        def epicDetails(ticket, statistics):
            data = {
                "id": ticket.id,
                "internalKey": ticket.internalKey,
                "summary": ticket.summary,
                "link": f"/jira/ticket/{ticket.internalKey}",
                "statistics": statistics,
            }
            return data

        projectTickets = Ticket.objects.filter(
            project__in=board.projects.all()
        ).select_related("column", "epic", "issueType")

        epicTickets = [pt for pt in projectTickets if pt.issueType.code == "EPIC"]

        epicTicketsList = [
            epicDetails(et, epicTicketStats(
                [
                    pt for pt in projectTickets
                    if pt.issueType.code != "EPIC" and pt.epic is not None and pt.epic.id == et.id
                ]
            )
                        )
            for et in epicTickets
        ]
        response = {
            "success": True,
            "data": {
                "epicTickets": epicTicketsList,
            }
        }
        return JsonResponse(response, status=HTTPStatus.OK)


class TeamChatMessagesApiEventVersion1Component(View):
    def get(self, *args, **kwargs):
        url = self.kwargs.get("url", None)

        teamChatMessageList = TeamChatMessage.objects.filter(
            team__url__exact=url
        ).select_related('user__profile').order_by('-id')[:100]

        # WIP: Group messages by day.
        # lst = []
        # lst2 = []
        #
        # for i in teamChatMessageList:
        #     createdDate = i.createdDttm.date()
        #
        #     if lst2 != [] and lst2[-1]['createdDate'] != createdDate:
        #         lst.append(lst2)
        #         lst2 = []
        #
        #     thisDict = {
        #         'id': i.id,
        #         'message': i.message,
        #         'sender': {
        #             'id': i.user_id,
        #             'fullName': i.user.get_full_name()
        #         },
        #         'time': i.getChatTime(),
        #         'createdDate': createdDate,
        #     }
        #
        #     if not lst2:
        #         lst2.append(thisDict)
        #     else:
        #         if lst2[-1]['createdDate'] == createdDate:
        #             lst2.append(thisDict)

        teamChatMessages = [
            {
                'id': message.id,
                'message': message.message,
                'sender': {
                    'id': message.user_id,
                    'fullName': message.user.get_full_name()
                },
                'time': message.getChatTime()
            }
            for message in teamChatMessageList
        ][::-1]

        response = {
            "success": True,
            "data": teamChatMessages
        }

        return JsonResponse(response, status=HTTPStatus.OK)


class AgileBoardColumnOperationApiEventVersion1Component(View):

    def canDeleteOrEdit(self, columnName):
        return columnName not in ["BACKLOG", "TO DO", "IN PROGRESS", "DONE"]

    def get(self, *args, **kwargs):
        boardId = self.kwargs.get("boardId", None)

        try:
            board = Board.objects.prefetch_related('boardSprints').get(id=boardId)
        except Board.DoesNotExist:
            response = {
                "success": False,
                "message": "Could not find a board for id: " + str(boardId)
            }
            return JsonResponse(response, status=HTTPStatus.NOT_FOUND)

        columnGroups = []
        for column in Column.objects.filter(Q(board_id=board.id), ~Q(internalKey="BACKLOG")).prefetch_related("columnStatus__columnStatusTickets"):

            columnStatusGroups = []
            for columnStatus in column.columnStatus.all():
                columnStatusData = {
                    "id": columnStatus.id,
                    "internalKey": columnStatus.internalKey,
                    "setResolution": columnStatus.setResolution,
                    "issues": columnStatus.columnStatusTickets.count(),
                    "colour": columnStatus.colour,
                    "category": columnStatus.category,
                }
                columnStatusGroups.append(columnStatusData)

            columnData = {
                "id": column.id,
                "internalKey": column.internalKey,
                "colour": column.colour,
                "category": column.category,
                "columnStatusGroups": columnStatusGroups,
                "canDelete": self.canDeleteOrEdit(column.internalKey),
            }
            columnGroups.append(columnData)

        # Get all unmapped status for this Board
        unMappedColumnStatus = [
            {
                "id": i.id,
                "internalKey": i.internalKey,
                "setResolution": i.setResolution,
                "issues": i.columnStatusTickets.count(),
                "colour": i.colour,
                "category": i.category
            }

            for i in ColumnStatus.objects.filter(board_id=boardId, column=None).prefetch_related("columnStatusTickets")
        ]

        unMappedStatusColumn = {
            "id": 0,
            "internalKey": "Unmapped Statuses",
            "colour": "#0052cc",
            "category": None,
            "columnStatusGroups": unMappedColumnStatus

        }

        response = {
            "success": True,
            "data": {
                "columnGroups": columnGroups,
                "unMappedStatusColumn": unMappedStatusColumn,
            }
        }
        return JsonResponse(response, status=HTTPStatus.OK)

    def post(self, *args, **kwargs):

        body = json.loads(self.request.body.decode())
        function = body.get("function")
        name = body.get("name")
        category = body.get("category")
        boardId = self.kwargs.get("boardId", None)

        try:
            board = Board.objects.prefetch_related('boardColumns', 'boardColumnStatus').get(id=boardId)
        except Board.DoesNotExist:
            response = {
                "success": False,
                "message": "Could not find a board for id: " + str(boardId)
            }
            return JsonResponse(response, status=HTTPStatus.NOT_FOUND)

        if not self.request.user in board.admins.all():
            response = {
                "success": False,
                "message": "Only admins can make changes to this board."
            }
            return JsonResponse(response, status=HTTPStatus.UNAUTHORIZED)

        def getCategory(obj, value):
            if value == "TODO":
                return obj.TODO
            if value == "IN_PROGRESS":
                return obj.IN_PROGRESS
            if value == "DONE":
                return obj.DONE
            raise NotImplemented

        def getColour(obj, value):
            if value == "TODO":
                return obj.TODO
            if value == "IN_PROGRESS":
                return obj.IN_PROGRESS
            if value == "DONE":
                return obj.DONE
            raise NotImplemented

        if function == "CREATE_BOARD_COLUMN" and name != "":
            boardColumns = board.boardColumns.all()
            existingColumn = [i for i in boardColumns if compare(i.internalKey.lower(), name.lower())]

            if len(existingColumn) == 0:
                Column.objects.create(
                    board_id=boardId,
                    internalKey=name,
                    category=getCategory(Column.Category, category),
                    colour=getColour(Column.Colour, category),
                    orderNo=board.boardColumns.count() + 1
                )
        elif function == "CREATE_COLUMN_STATUS" and name != "":
            boardColumnStatus = board.boardColumnStatus.all()
            existingColumnStatus = [i for i in boardColumnStatus if compare(i.internalKey.lower(), name.lower())]

            if len(existingColumnStatus) == 0:
                newColumnStatus = ColumnStatus(
                    internalKey=name,
                    board_id=boardId,
                    category=getCategory(ColumnStatus.Category, category),
                    colour=getColour(ColumnStatus.Colour, category),
                )

                # if the status name matches with any of the column name, then add it to that column.
                boardColumns = board.boardColumns.all()
                existingColumn = [i for i in boardColumns if compare(i.internalKey.lower(), name.lower())]

                if len(existingColumn) != 0:
                    newColumnStatus.column = existingColumn[0]
                newColumnStatus.save()

        response = {
            "success": True,
        }
        return JsonResponse(response, status=HTTPStatus.OK)

    def put(self, *args, **kwargs):
        boardId = self.kwargs.get("boardId", None)
        try:
            board = Board.objects.get(id=boardId)
        except Board.DoesNotExist:
            response = {
                "success": False,
                "message": "Could not find a board for id: " + str(boardId)
            }
            return JsonResponse(response, status=HTTPStatus.NOT_FOUND)

        if not self.request.user in board.admins.all():
            response = {
                "success": False,
                "message": "Only admins can make changes to this board."
            }
            return JsonResponse(response, status=HTTPStatus.UNAUTHORIZED)

        put = QueryDict(self.request.body)
        columnAndStatus = json.loads(put.get('columnAndStatus'))
        columnsInOrder = [int(i['columnId']) for i in columnAndStatus if i['columnId'] != "0"]
        setResolutionCheckedStatus = put.getlist('checkedBoxes[]')

        columns = Column.objects.filter(Q(board_id=board.id), ~Q(internalKey="BACKLOG"))
        for i in columns:
            i.orderNo = columnsInOrder.index(i.pk)

        Column.objects.bulk_update(columns, ['orderNo'])

        for i in columnAndStatus:
            thisColumnsColumnStatus = ColumnStatus.objects.filter(id__in=i['statusIds'], board_id=board.id)
            if i['columnId'] == "0":
                thisColumnsColumnStatus.update(column=None)
            else:
                thisColumnsColumnStatus.update(column_id=i['columnId'])

        thisBoardsColumnStatus = ColumnStatus.objects.filter(board_id=board.id)
        for columnStatus in thisBoardsColumnStatus:
            columnStatus.setResolution = str(columnStatus.id) in setResolutionCheckedStatus

        ColumnStatus.objects.bulk_update(thisBoardsColumnStatus, ['setResolution'])

        response = {
            "success": True,
        }
        return JsonResponse(response, status=HTTPStatus.OK)

    def delete(self, *args, **kwargs):
        boardId = self.kwargs.get("boardId", None)
        try:
            board = Board.objects.get(id=boardId)
        except Board.DoesNotExist:
            response = {
                "success": False,
                "message": "Could not find a board for id: " + str(boardId)
            }
            return JsonResponse(response, status=HTTPStatus.NOT_FOUND)

        if not self.request.user in board.admins.all():
            response = {
                "success": False,
                "message": "Only admins can make changes to this board."
            }
            return JsonResponse(response, status=HTTPStatus.UNAUTHORIZED)

        put = json.loads(self.request.body)
        function = put.get("function")
        columnId = put.get("columnId")

        if function == "DELETE_COLUMN":
            columns = Column.objects.get(Q(id=columnId, board_id=board.id), ~Q(internalKey="BACKLOG"))
            ColumnStatus.objects.filter(board_id=board.id, column_id=columns.id).update(column=None)
            columns.delete()

        response = {
            "success": True,
        }
        return JsonResponse(response, status=HTTPStatus.OK)


@method_decorator(csrf_exempt, name='dispatch')
class SprintObjectApiEventVersion1Component(View):

    def post(self, *args, **kwargs):
        boardId = self.kwargs.get("boardId", None)

        try:
            board = Board.objects.prefetch_related('boardSprints').get(id=boardId)
        except Board.DoesNotExist:
            response = {
                "success": False,
                "message": "Could not find a board for id: " + str(boardId)
            }
            return JsonResponse(response, status=HTTPStatus.NOT_FOUND)

        recentSprint = board.boardSprints.last()
        sprintCount = 1 if recentSprint is None else board.boardSprints.count() + 1

        Sprint.objects.create(
            board=board,
            internalKey=f'{board.internalKey} Sprint {sprintCount}',
            orderNo=sprintCount,
        )
        response = {
            "success": True,
        }
        return JsonResponse(response, status=HTTPStatus.OK)

    def put(self, *args, **kwargs):
        boardId = self.kwargs.get("boardId", None)

        try:
            board = Board.objects.prefetch_related('boardSprints', 'boardColumns').get(id=boardId)
        except Board.DoesNotExist:
            response = {
                "success": False,
                "message": "Could not find a board for id: " + str(boardId)
            }
            return JsonResponse(response, status=HTTPStatus.NOT_FOUND)

        put = QueryDict(self.request.body)
        sprintId = put.get("sprintId")
        function = put.get("function")

        if board.type != Board.Types.SCRUM:
            response = {
                "success": False,
                "message": "Cannot perform sprint actions for non SCRUM boards."
            }
            return JsonResponse(response, status=HTTPStatus.OK)

        if function == 'COMPLETE_SPRINT':
            # TODO: OPTIMISE THIS!!!
            """
                get all the tickets which are not in DONE. move them to next sprint if available else create one.
                set the current sprint to complete.
            """
            openSprints = Sprint.objects.filter(board__id=boardId, isComplete=False).order_by('orderNo')

            try:
                nextSprint = openSprints[1]
            except IndexError:
                sprintCount = board.boardSprints.count() + 1
                nextSprint = Sprint.objects.create(
                    board=board,
                    internalKey=f'{board.internalKey} Sprint {sprintCount}',
                    orderNo=sprintCount,
                )

            currentSprint = databaseOperations.getObjectByIdOrNone(openSprints, sprintId)

            unDoneTicketIds = [
                ticket.id
                for ticket in currentSprint.tickets.all()
                if (ticket.resolution.code in ["UNRESOLVED", "REOPENED"] or ticket.columnStatus.category != ColumnStatus.Category.DONE) and ticket.issueType.code != "EPIC"
            ]

            currentSprint.removeTicketsFromSprint(unDoneTicketIds)
            currentSprint.isComplete = True
            currentSprint.save()
            nextSprint.addTicketsToSprint(unDoneTicketIds)

        elif function == 'DELETE_SPRINT':
            # TODO: Bug: when sprint is deleted the remaining tickets are not showing up in the backlog
            sprint = Sprint.objects.get(id=sprintId, board__id=boardId, isComplete=False)
            sprintTicketsId = sprint.tickets.values_list('id', flat=True)
            sprint.removeTicketsFromSprint(sprintTicketsId)
            sprint.delete()
            backLogColumn = databaseOperations.getObjectByInternalKey(board.boardColumns.all(), 'BACKLOG')
            Ticket.objects.filter(id__in=list(sprintTicketsId)).update(board_id=boardId, column_id=backLogColumn.id)

        response = {
            "success": True,
        }
        return JsonResponse(response, status=HTTPStatus.OK)


class TicketObjectDetailApiEventVersion1Component(View):

    def get(self, *args, **kwargs):
        ticketId = self.kwargs.get("ticketId")

        try:
            ticket = Ticket.objects.select_related(
                'project',
                'issueType',
                'resolution',
                'columnStatus__board',
                'priority',
                'assignee__profile', 'reporter__profile'
            ).prefetch_related('label', 'component', 'watchers').get(id=ticketId)
        except Ticket.DoesNotExist:
            response = {
                "success": False,
                "message": "Could not find a ticket with id: {}".format(ticketId)
            }
            return JsonResponse(response, status=HTTPStatus.NOT_FOUND)

        ticketDetails = {
            "id": ticket.id,
            "internalKey": ticket.internalKey,
            "summary": ticket.summary,
            "description": ticket.description,
            "createdDate": datetime.strftime(ticket.createdDttm, '%d %B %Y, %I:%M %p'),
            "modifiedDate": datetime.strftime(ticket.modifiedDttm, '%d %B %Y, %I:%M %p'),
            "link": ticket.getTicketUrl(),
            "storyPoints": ticket.storyPoints,
            "fixVersion": ticket.fixVersion,
            "project": ticket.project.serializeProjectVersion1(),
            "issueType": ticket.issueType.serializeComponentVersion1(),
            "priority": ticket.priority.serializeComponentVersion1(),
            "resolution": ticket.resolution.serializeComponentVersion1(),
            "status": ticket.columnStatus.serializeColumnStatusVersion1(),
            "workflow": [
                status.serializeColumnStatusVersion1()
                for status in ticket.columnStatus.board.boardColumnStatus.all()
            ],
            "assignee": generalOperations.serializeUserVersion2(ticket.assignee),
            "reporter": generalOperations.serializeUserVersion2(ticket.reporter),
            "components": [component.serializeComponentVersion1() for component in ticket.component.all()],
            "labels": [label.serializeLabelVersion1() for label in ticket.label.all()],
            'watchers': {
                'counter': ticket.watchers.count(),
                'isWatching': self.request.user in ticket.watchers.all(),
                'message': getWatchersMessage(self.request.user, ticket.watchers.all()),
            }
        }

        response = {
            "success": True,
            "data": ticketDetails,
        }

        return JsonResponse(response, status=HTTPStatus.OK)

    def post(self, *args, **kwargs):
        body = json.loads(self.request.body.decode())
        ticket = Ticket()

        thisProject = Project.objects.filter(id=body["project"]).first()
        newTicketNumber = thisProject.projectTickets.count() + 1
        ticket.internalKey = thisProject.code + "-" + str(newTicketNumber)
        ticket.orderNo = newTicketNumber

        for key, value in body.items():
            value = value or None

            if hasattr(ticket, f"{key}_id"):
                setattr(ticket, f"{key}_id", int(value))
            elif hasattr(ticket, f"{key}"):
                setattr(ticket, f"{key}", value)

        ticket.save()
        response = {
            "success": True,
        }
        return JsonResponse(response, status=HTTPStatus.OK)


class ProjectObjectApiEventVersion1Component(View):

    def get(self, *args, **kwargs):
        projectId = int(self.kwargs.get("projectId", 0))

        if projectId == 0:
            projects = Project.objects.all()
        else:
            projects = Project.objects.filter(id=projectId)

        response = {
            "success": True,
            "data": {
                "projects": [
                    project.serializeProjectVersion1()
                    for project in projects
                ]
            }
        }
        return JsonResponse(response, status=HTTPStatus.OK)


class LabelObjectApiEventVersion1Component(View):

    def get(self, *args, **kwargs):
        labelId = None
        labels = Label.objects.all() if labelId is None else Label.objects.filter(id=labelId)

        response = {
            "success": True,
            "data": {
                "labels": [
                    label.serializeLabelVersion1()
                    for label in labels
                ]
            }
        }
        return JsonResponse(response, status=HTTPStatus.OK)


class ColumnStatusObjectApiEventVersion1Component(View):

    def get(self, *args, **kwargs):
        statusId = None
        getUniqueOnly = True
        statusList = ColumnStatus.objects.all() if statusId is None else ColumnStatus.objects.filter(id=statusId)

        if getUniqueOnly:
            uniqueStatus = []
            for item in statusList:
                if item.internalKey.casefold() not in [i.internalKey.casefold() for i in uniqueStatus]:
                    uniqueStatus.append(item)

            statusList = uniqueStatus

        response = {
            "success": True,
            "data": {
                "status": [
                    status.serializeColumnStatusVersion1()
                    for status in statusList
                ]
            }
        }
        return JsonResponse(response, status=HTTPStatus.OK)


class BoardObjectApiEventVersion1Component(View):

    def get(self, *args, **kwargs):
        boardId = int(self.kwargs.get("boardId", 0))

        if boardId == 0:
            boards = Board.objects.all()
        else:
            boards = Board.objects.filter(id=boardId)

        response = {
            "success": True,
            "data": {
                "boards": [
                    board.serializeBoardVersion1()
                    for board in boards
                ]
            }
        }
        return JsonResponse(response, status=HTTPStatus.OK)


class UserObjectApiEventVersion1Component(View):

    def get(self, *args, **kwargs):
        userId = int(self.kwargs.get("userId", 0))

        if userId == 0:
            users = User.objects.all()
        else:
            users = User.objects.filter(id=userId)

        response = {
            "success": True,
            "data": {
                "users": [
                    {
                        "id": user.id,
                        "firstName": user.first_name,
                        "lastName": user.last_name,
                    }
                    for user in users
                ]
            }
        }
        return JsonResponse(response, status=HTTPStatus.OK)


class TicketAttachmentObjectApiEventVersion1Component(View):

    def delete(self, *args, **kwargs):
        body = json.loads(self.request.body)
        TicketAttachment.objects.filter(id=body['id']).delete()
        response = {
            "success": True,
        }
        return JsonResponse(response, status=HTTPStatus.OK)


class ProfileObjectApiEventVersion1Component(View):

    def get(self, *args, **kwargs):
        profileId = int(self.request.GET['id'])

        if profileId == 0:
            profiles = Profile.objects.select_related('user')
        else:
            profiles = Profile.objects.filter(id=profileId)

        response = {
            "success": True,
            "data": {
                "profiles": [
                    {
                        "id": profile.id,
                        "firstName": profile.user.first_name,
                        "lastName": profile.user.last_name,
                    }
                    for profile in profiles
                ]
            }
        }
        return JsonResponse(response, status=HTTPStatus.OK)


@method_decorator(csrf_exempt, name='dispatch')
class TicketObjectBulkCreateApiEventVersion1Component(View):

    def post(self, *args, **kwargs):
        body = json.loads(self.request.body)
        resolution = Component.objects.get(componentGroup__code='TICKET_RESOLUTIONS', code="UNRESOLVED")
        priority = Component.objects.get(componentGroup__code='TICKET_PRIORITY', code="MEDIUM")
        reporter = User.objects.get(username="admin")
        board = Board.objects.first()

        for ticket in body['data']['tickets']:
            project = Project.objects.filter(code__icontains=ticket['projectCode']).first()

            if project is None:
                continue

            newTicketNumber = project.projectTickets.count() + 1

            newTicket = Ticket()
            newTicket.internalKey = project.code + "-" + str(newTicketNumber)
            newTicket.summary = ticket["summary"]
            newTicket.description = ticket["description"]
            newTicket.resolution = resolution
            newTicket.project = project
            newTicket.reporter = reporter
            newTicket.storyPoints = ticket["storyPoints"]
            newTicket.issueType = Component.objects.get(componentGroup__code='TICKET_ISSUE_TYPE',
                                                        internalKey=ticket["issueType"])
            newTicket.priority = priority
            newTicket.board = board
            newTicket.column = Column.objects.get(board=board, internalKey='TO DO')
            newTicket.orderNo = newTicketNumber
            newTicket.save()
        return JsonResponse({}, status=HTTPStatus.OK)


def serializeTickets(tickets, data, skipOldCompletedTickets=True):
    newData = [
        {
            "id": ticket.id,
            "summary": ticket.summary,
            "internalKey": ticket.internalKey,
            "fixVersion": ticket.fixVersion if ticket.fixVersion else None,
            "link": f"/jira/ticket/{ticket.internalKey}",
            "storyPoints": ticket.storyPoints if ticket.storyPoints is not None else "-",
            "column": ticket.column.internalKey if ticket.column is not None else None,
            "modifiedDttm": str(ticket.modifiedDttm.date()),
            "issueType": ticket.issueType.serializeComponentVersion1(),
            "priority": ticket.priority.serializeComponentVersion1(),
            "resolution": ticket.resolution.serializeComponentVersion1(),
            "assignee": generalOperations.serializeUserVersion1(ticket.assignee),
            "epic": {
                "id": ticket.epic.id,
                "internalKey": ticket.epic.internalKey,
                "summary": ticket.epic.summary,
                "colour": ticket.epic.colour,
                "link": f"/jira/ticket/{ticket.epic.internalKey}",
            } if ticket.epic is not None else None,
        }
        for ticket in tickets
    ]

    # TODO: Check if this is useful.
    today = datetime.now().date()
    for i in newData:
        if skipOldCompletedTickets:
            modifiedDate = datetime.strptime(i['modifiedDttm'], '%Y-%m-%d').date()
            if (today - modifiedDate).days <= 14:
                data.append(i)
            continue
        data.append(i)

    return


def getWatchersMessage(user, watchers):
    if not user.is_authenticated:
        return "You have to be logged in to watch an issue."
    if user in watchers:
        return "You are watching this issue. Click to stop watching this issue."
    return "You are not watching this issue. Click to watch this issue."


def serializeTicketsIntoChunks(tickets):
    if tickets.count() == 0:
        return []

    data = []
    JOBS = []
    MAX_THREADS = 4
    chunkSize = tickets.count() // MAX_THREADS

    if chunkSize == 0:
        serializeTickets(tickets, data)
        return data

    ticketsChunks = [tickets[i:i + chunkSize] for i in range(0, len(tickets), chunkSize)]

    for index in ticketsChunks:
        JOBS.append(threading.Thread(target=serializeTickets, args=(index, data,)))

    for j in JOBS:
        j.start()

    for j in JOBS:
        j.join()

    return data
