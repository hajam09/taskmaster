import json
import threading
from datetime import datetime
from http import HTTPStatus

from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import QueryDict, JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from accounts.models import Team, Component
from jira.models import Board, Column, Label, Ticket, Project, Sprint, TicketComment
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
        ticketComment.creator = self.request.user or None
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


#
# @method_decorator(csrf_exempt, name='dispatch')
# class TicketObjectBaseDataUpdateApiEventVersion1Component(View):
#
#     def put(self, *args, **kwargs):
#         ticketId = self.kwargs.get("ticketId", None)
#         put = QueryDict(self.request.body)
#
#         try:
#             ticket = Ticket.objects.get(id=ticketId)
#         except Ticket.DoesNotExist:
#             response = {
#                 "success": False,
#                 "message": "Unable to find the ticket to update"
#             }
#             return JsonResponse(response, status=HTTPStatus.NOT_FOUND)
#
#         summary = put.get("ticketSummary", ticket.summary)
#         description = put.get("ticketDescription", ticket.description)
#         userImpact = put.get("ticketUserImpact", ticket.userImpact)
#         releaseImpact = put.get("ticketReleaseImpact", ticket.releaseImpact)
#         automatedTestingReason = put.get("ticketAutomaticTestingReason", ticket.automatedTestingReason)
#
#         ticket.summary = summary
#         ticket.description = description
#         ticket.userImpact = userImpact
#         ticket.releaseImpact = releaseImpact
#         ticket.automatedTestingReason = automatedTestingReason
#
#         ticket.save(update_fields=['summary', 'description', 'userImpact', 'releaseImpact', 'automatedTestingReason'])
#
#         response = {
#             "success": True,
#         }
#         return JsonResponse(response, status=HTTPStatus.OK)
#
#
# @method_decorator(csrf_exempt, name='dispatch')
# class TicketObjectForIssuesInTheEpicTicketApiEventVersion1Component(View):
#
#     def post(self, *args, **kwargs):
#         projectId = self.request.POST.get("project-id", None)
#         ticketSummary = self.request.POST.get("ticket-summary", None)
#         issueType = self.request.POST.get("issue-type", None)
#         epicTicketId = self.request.POST.get("epic-ticket-id", None)
#
#         ticketIssueTypeComponents = cache.get("ticketIssueTypeComponents")
#         ticketSecurityComponents = cache.get("ticketSecurityComponents")
#         ticketStatusComponents = cache.get("ticketStatusComponents")
#         ticketPriorityComponents = cache.get("ticketPriorityComponents")
#
#         project = Project.objects.get(id=projectId)
#         newTicketNumber = project.projectTickets.count() + 1
#
#         ticket = Ticket()
#         ticket.internalKey = project.code + "-" + str(newTicketNumber)
#         ticket.summary = ticketSummary
#         ticket.project = project
#         ticket.reporter = self.request.user
#         ticket.issueType = next((i for i in ticketIssueTypeComponents if i.code == issueType), None)
#         ticket.securityLevel = next((i for i in ticketSecurityComponents if i.code == "EXTERNAL"), None)
#         ticket.status = next((i for i in ticketStatusComponents if i.code == "BACKLOG"), None)
#         ticket.priority = next((i for i in ticketPriorityComponents if i.code == "MEDIUM"), None)
#
#         if epicTicketId is not None:
#             epicTicket = Ticket.objects.get(id=epicTicketId, issueType__code="EPIC")
#             ticket.board = epicTicket.board
#             ticket.column = epicTicket.column
#             ticket.epic = epicTicket
#
#         ticket.save()
#
#         response = {
#             "success": True,
#             "data": {
#                 "id": ticket.id,
#                 "internalKey": ticket.internalKey,
#                 "summary": ticket.summary,
#                 "link": "/jira2/ticket/" + str(ticket.internalKey),
#                 "issueType": {
#                     "internalKey": ticket.issueType.internalKey,
#                     "icon": "/static/" + ticket.issueType.icon,
#                 },
#                 "priority": {
#                     "internalKey": ticket.priority.internalKey,
#                     "icon": "/static/" + ticket.priority.icon
#                 },
#             }
#         }
#         return JsonResponse(response, status=HTTPStatus.OK)
#
#
@method_decorator(csrf_exempt, name='dispatch')
class KanbanBoardDetailsAndItemsApiEventVersion1Component(View):

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

        columns = Column.objects.filter(Q(board_id=board.id), ~Q(internalKey="BACKLOG")).prefetch_related('columnTickets')
        columnsList = []

        for column in columns:
            allColumnTickets = column.columnTickets.filter(~Q(issueType__code="EPIC")).select_related(
                'assignee__profile',
                'column', 'epic',
                'issueType',
                'priority',
                'resolution')

            tickets = []
            serializeTickets(allColumnTickets, tickets)
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
class KanbanBoardTicketColumnUpdateApiEventVersion1Component(View):

    def put(self, *args, **kwargs):
        put = QueryDict(self.request.body)

        columnId = put.get("column-id")
        ticketId = put.get("ticket-id")

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
class KanbanBoardBacklogActiveTicketsApiEventVersion1Component(View):

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

        columns = Column.objects.filter(Q(board_id=board.id), ~Q(internalKey="BACKLOG")).prefetch_related('columnTickets')
        activeTickets = []

        for column in columns:
            allColumnTickets = column.columnTickets.filter(~Q(issueType__code="EPIC")).select_related(
                'assignee__profile',
                'column',
                'epic', 'issueType',
                'priority',
                'resolution')

            data = []
            serializeTickets(allColumnTickets, data, False)
            activeTickets.extend(data)

        response = {
            "success": True,
            "data": {
                "tickets": activeTickets,
            }
        }
        return JsonResponse(response, status=HTTPStatus.OK)


@method_decorator(csrf_exempt, name='dispatch')
class KanbanBoardBacklogInActiveTicketsApiEventVersion1Component(View):

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

        column = Column.objects.prefetch_related('columnTickets').get(board_id=board.id, internalKey__icontains="BACKLOG")
        inActiveTickets = []

        columnTickets = column.columnTickets.filter(~Q(issueType__code="EPIC")).select_related('assignee__profile',
                                                                                               'column',
                                                                                               'epic', 'issueType',
                                                                                               'priority',
                                                                                               'resolution')
        serializeTickets(columnTickets, inActiveTickets)

        response = {
            "success": True,
            "data": {
                "tickets": inActiveTickets,
            }
        }
        return JsonResponse(response, status=HTTPStatus.OK)


@method_decorator(csrf_exempt, name='dispatch')
class ScrumBoardSprintTicketsApiEventVersion1Component(View):

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

        if board.type != Board.Types.SCRUM:
            raise Exception

        sprints = []
        today = timezone.now().date()
        queries = Q(startDate__gte=today) | Q(startDate__lte=today, endDate__gte=today)
        activeAndUpcomingSprints = board.boardSprints.filter(queries).prefetch_related('tickets')

        for sprint in activeAndUpcomingSprints:
            serializedTickets = []
            sprintTickets = sprint.tickets.filter(~Q(issueType__code="EPIC")).select_related('assignee__profile',
                                                                                             'column',
                                                                                             'epic', 'issueType',
                                                                                             'priority',
                                                                                             'resolution')
            serializeTickets(sprintTickets, serializedTickets)
            sprintData = {
                "id": sprint.id,
                "internalKey": sprint.internalKey,
                "isActive": sprint.startDate <= today <= sprint.endDate,
                "tickets": serializedTickets
            }
            sprints.append(sprintData)

        response = {
            "success": True,
            "data": {
                "sprints": sprints,
            }
        }
        return JsonResponse(response, status=HTTPStatus.OK)

    def put(self, *args, **kwargs):
        # TODO: NOT DONE
        boardId = self.kwargs.get("boardId", None)

        try:
            board = Board.objects.prefetch_related('boardSprints').get(id=boardId)
        except Board.DoesNotExist:
            response = {
                "success": False,
                "message": "Could not find a board for id: " + str(boardId)
            }
            return JsonResponse(response, status=HTTPStatus.NOT_FOUND)

        if board.type != Board.Types.SCRUM:
            raise Exception

        ticket = Ticket()

        for sprint in board.boardSprints.all():
            sprint.tickets.remove(ticket)

        thisSprint = Sprint()
        thisSprint.tickets.add(ticket)


@method_decorator(csrf_exempt, name='dispatch')
class KanbanBoardActiveEpicLessTicketsApiEventVersion1Component(View):
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

        columns = Column.objects.filter(Q(board_id=board.id), ~Q(internalKey="BACKLOG")).prefetch_related(
            'columnTickets')
        activeTickets = []

        for column in columns:
            allColumnTickets = column.columnTickets.filter(~Q(issueType__code="EPIC"), Q(epic=None)).select_related(
                'assignee__profile',
                'column',
                'epic', 'issueType',
                'priority',
                'resolution')

            data = []
            serializeTickets(allColumnTickets, data, False)
            activeTickets.extend(data)

        response = {
            "success": True,
            "data": {
                "tickets": activeTickets,
            }
        }
        return JsonResponse(response, status=HTTPStatus.OK)


@method_decorator(csrf_exempt, name='dispatch')
class KanbanBoardInActiveEpicLessTicketsApiEventVersion1Component(View):
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

        column = Column.objects.prefetch_related('columnTickets').get(board_id=board.id, internalKey__icontains="BACKLOG")
        inActiveTickets = []

        columnTickets = column.columnTickets.filter(~Q(issueType__code="EPIC"), Q(epic=None)).select_related(
            'assignee__profile',
            'column',
            'epic', 'issueType',
            'priority',
            'resolution')
        serializeTickets(columnTickets, inActiveTickets)

        response = {
            "success": True,
            "data": {
                "tickets": inActiveTickets,
            }
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

        def epicTicketsStats(childTicket):
            todo = inProgress = done = 0

            for ct in childTicket:
                if ct.column.internalKey == "TO DO":
                    todo += ct.storyPoints
                elif ct.column.internalKey == "IN PROGRESS":
                    inProgress += ct.storyPoints
                elif ct.column.internalKey == "DONE":
                    done += ct.storyPoints
            data = {
                'todo': todo,
                'inProgress': inProgress,
                'done': done,
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

        projectTickets = Ticket.objects.filter(project__in=board.projects.all()).select_related('column', 'epic',
                                                                                                'issueType')
        epicTickets = [pt for pt in projectTickets if pt.issueType.code == "EPIC"]
        epicTicketsList = [
            epicDetails(et, epicTicketsStats(
                [pt for pt in projectTickets if pt.epic is not None and pt.epic.id == et.id]))
            for et in epicTickets
        ]
        response = {
            "success": True,
            "data": {
                "epicTickets": epicTicketsList,
            }
        }
        return JsonResponse(response, status=HTTPStatus.OK)

#
# @method_decorator(csrf_exempt, name='dispatch')
# class BoardObjectDetailsApiEventVersion1Component(View):
#
#     def get(self, *args, **kwargs):
#         boardId = self.kwargs.get("boardId", None)
#
#         try:
#             board = Board.objects.get(id=boardId)
#         except Board.DoesNotExist:
#             response = {
#                 "success": False,
#                 "message": "Could not find a board for id: " + str(boardId)
#             }
#             return JsonResponse(response, status=HTTPStatus.NOT_FOUND)
#
#         response = {
#             "success": True,
#             "data": {
#                 "id": board.id,
#                 "internalKey": board.internalKey,
#                 "url": board.url,
#                 "createdDttm": board.createdDttm,
#                 "isPrivate": board.isPrivate,
#                 "members": [
#                     {
#                         "id": i.pk,
#                         "firstName": i.first_name,
#                         "lastName": i.last_name,
#                         "icon": i.developerProfile.profilePicture.url
#                     }
#                     for i in board.members.all()
#                 ],
#                 "admins": [
#                     {
#                         "id": i.pk,
#                         "firstName": i.first_name,
#                         "lastName": i.last_name,
#                         "icon": i.developerProfile.profilePicture.url
#                     }
#                     for i in board.admins.all()
#                 ],
#             }
#         }
#         return JsonResponse(response, status=HTTPStatus.OK)
#
#


@method_decorator(csrf_exempt, name='dispatch')
class SprintObjectApiEventVersion1Component(View):

    def post(self, *args, **kwargs):
        # TODO: Manual test needed.
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
        sprintCount = 0 if recentSprint is None else board.boardSprints.count() + 1
        startDate = recentSprint.endDate if recentSprint.endDate >= timezone.now().date() else timezone.now()
        endDate = startDate + timezone.timedelta(days=14)

        sprint = Sprint.objects.create(
            board=board,
            internalKey=f'{board.internalKey} Sprint {sprintCount}',
            startDate=startDate,
            endDate=endDate
        )
        response = {
            "success": True,
            "data": {
                "sprint": {
                    "id": sprint.id,
                    "board": {
                        "id": sprint.board.id,
                        "internalKey": sprint.board.internalKey,
                        "url": sprint.board.url,
                    },
                    "internalKey": sprint.internalKey,
                    "startDate": sprint.startDate.date(),
                    "endDate": sprint.endDate.date()
                },
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
