import imghdr
import json
import threading
from datetime import datetime
from http import HTTPStatus

from django.contrib import messages
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models import Q
from django.http import QueryDict, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from accounts.models import Team, Component, TeamChatMessage
from jira.models import Board, Column, Label, Ticket, Project, Sprint, TicketComment, TicketAttachment
from taskmaster.operations import databaseOperations


@method_decorator(csrf_exempt, name='dispatch')
class BoardSettingsViewGeneralDetailsApiEventVersion1Component(View):

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

        boardName = put.get("board-name", board.internalKey)
        boardProjects = put.getlist("board-projects[]", [])
        boardAdmins = put.getlist("board-admins[]", [])
        boardMembers = put.getlist("board-members[]", [])
        boardVisibility = put.get("board-visibility", board.isPrivate)

        board.internalKey = boardName
        board.isPrivate = boardVisibility == 'visibility-members'

        # just passing the ids will do the job
        board.projects.clear()
        board.projects.add(*boardProjects)

        board.admins.clear()
        board.admins.add(*boardAdmins)

        board.members.clear()
        board.members.add(*boardMembers)

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


@method_decorator(csrf_exempt, name='dispatch')
class TeamsObjectApiEventVersion1Component(View):
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
            'creator': {
                'id': ticketComment.creator.id,
                'fullName': ticketComment.creator.get_full_name(),
                'icon': ticketComment.creator.profile.profilePicture.url
            }

        }

        response = {
            'success': True,
            'data': data
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


@method_decorator(csrf_exempt, name='dispatch')
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
                'creator': {
                    'id': comment.creator.id,
                    'fullName': comment.creator.get_full_name(),
                    'icon': comment.creator.profile.profilePicture.url
                }
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
        ticket.resolution = Component.objects.get(componentGroup__code='TICKET_RESOLUTIONS', code="UNRESOLVED")
        ticket.project = parentTicket.project
        ticket.reporter = self.request.user
        ticket.issueType = Component.objects.get(componentGroup__code='TICKET_ISSUE_TYPE', code="SUB_TASK")
        ticket.priority = Component.objects.get(componentGroup__code='TICKET_PRIORITY', code="MEDIUM")
        ticket.board = parentTicket.board
        ticket.column = Column.objects.get(board=parentTicket.board, internalKey='TO DO')
        ticket.orderNo = newTicketNumber
        ticket.save()

        # TODO: Update to the current sprint
        parentTicket.subTask.add(ticket)

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


@method_decorator(csrf_exempt, name='dispatch')
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

                if childTicket.column.internalKey == "BACKLOG" or childTicket.column.internalKey == "TO DO":
                    notStarted += 1

                if childTicket.column.internalKey == "IN PROGRESS":
                    inProgress += 1

                # TODO: What if ticket status can be used to determined the finish line.
                if childTicket.column.internalKey == "DONE":
                    completed += 1

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


@method_decorator(csrf_exempt, name='dispatch')
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

        if function == 'COMPLETE_SPRINT':
            # TODO: OPTIMISE THIS!!!
            """
                get all the tickets which are not in DONE. move them to next sprint if available else create one.
                set the current sprint to complete.
            """
            openSprints = Sprint.objects.filter(
                board__id=boardId, isComplete=False,
            ).order_by('orderNo')

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
                if ticket.resolution.code != "RESOLVED" and ticket.issueType.code != "EPIC"
            ]

            currentSprint.removeTicketsFromSprint(unDoneTicketIds)
            currentSprint.isComplete = True
            currentSprint.save()
            nextSprint.addTicketsToSprint(unDoneTicketIds)

        elif function == 'DELETE_SPRINT':
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
            "issueType": {
                "internalKey": ticket.issueType.internalKey,
                "icon": ticket.issueType.icon,
            },
            "priority": {
                "internalKey": ticket.priority.internalKey,
                "icon": ticket.priority.icon
            },
            "resolution": {
                "internalKey": ticket.resolution.internalKey,
                "code": ticket.resolution.code,
            },
            "epic": {
                "id": ticket.epic.id,
                "internalKey": ticket.epic.internalKey,
                "summary": ticket.epic.summary,
                "colour": ticket.epic.colour,
                "link": f"/jira/ticket/{ticket.epic.internalKey}",
            } if ticket.epic is not None else None,
            "assignee": {
                "id": ticket.assignee.pk,
                "firstName": ticket.assignee.first_name,
                "lastName": ticket.assignee.last_name,
                "icon": ticket.assignee.profile.profilePicture.url
            } if ticket.assignee is not None else None,
        }
        for ticket in tickets
    ]

    today = datetime.now().date()
    for i in newData:
        if skipOldCompletedTickets:
            modifiedDate = datetime.strptime(i['modifiedDttm'], '%Y-%m-%d').date()
            if (today - modifiedDate).days <= 14:
                data.append(i)
            continue
        data.append(i)

    return


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
