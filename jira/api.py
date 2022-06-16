import json
import threading
from datetime import datetime
from datetime import timedelta
from http import HTTPStatus

from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models import Q
from django.http import QueryDict, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from accounts.models import Component
from jira.models import Board, Column, Label, Ticket, Project
from taskmaster.operations import databaseOperations


@method_decorator(csrf_exempt, name='dispatch')
class BoardSettingsViewGeneralDetailsApiEventVersion1Component(View):

    def put(self, *args, **kwargs):
        # MANUAL_TESTED
        url = self.kwargs.get("url", None)
        put = QueryDict(self.request.body)

        try:
            board = Board.object.get(url=url)
        except Board.DoesNotExist:
            response = {
                "success": False,
                "message": "Could not find a board with url/id: ".format(url)
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
            board = Board.object.get(url=url)
        except Board.DoesNotExist:
            response = {
                "success": False,
                "message": "Could not find a board with url/id: ".format(url)
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
            board = Board.object.get(url=url)
        except Board.DoesNotExist:
            response = {
                "success": False,
                "message": "Could not find a board with url/id: ".format(url)
            }
            return JsonResponse(response, status=HTTPStatus.NOT_FOUND)

        newColumnName = self.request.POST.get("column-name", None)

        if newColumnName is not None:
            boardColumns = board.boardColumns.all()

            existingColumn = [i for i in boardColumns if i.internalKey.lower() == newColumnName.lower()]
            if len(existingColumn) == 0:
                newColumn = Column.object.create(
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
            board = Board.object.get(url=url)
        except Board.DoesNotExist:
            response = {
                "success": False,
                "message": "Could not find a board with url/id: ".format(url)
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
            Board.object.get(url=url)
        except Board.DoesNotExist:
            response = {
                "success": False,
                "message": "Could not find a board with url/id: ".format(url)
            }
            return JsonResponse(response, status=HTTPStatus.NOT_FOUND)

        put = QueryDict(self.request.body)
        columnId = put.get("column-id", None)
        column = Column.object.filter(id=columnId).first()

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

        column.deleteFl = True
        column.save(update_fields=['deleteFl'])

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
            board = Board.object.get(url=url)
        except Board.DoesNotExist:
            response = {
                "success": False,
                "message": "Could not find a board with url/id: ".format(url)
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
            board = Board.object.get(url=url)
        except Board.DoesNotExist:
            response = {
                "success": False,
                "message": "Could not find a board with url/id: ".format(url)
            }
            return JsonResponse(response, status=HTTPStatus.NOT_FOUND)

        newLabelName = self.request.POST.get("label-name", None)

        if newLabelName is None:
            return JsonResponse({}, status=HTTPStatus.ACCEPTED)

        newLabel = Label.object.create(
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
            board = Board.object.get(url=url)
        except Board.DoesNotExist:
            response = {
                "success": False,
                "message": "Could not find a board with url/id: ".format(url)
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
            board = Board.object.get(url=url)
        except Board.DoesNotExist:
            response = {
                "success": False,
                "message": "Could not find a board with url/id: ".format(url)
            }
            return JsonResponse(response, status=HTTPStatus.NOT_FOUND)

        put = QueryDict(self.request.body)
        labelId = put.get("label-id", None)

        Label.object.filter(id=labelId, board=board).update(deleteFl=True)

        response = {
            "success": True
        }
        return JsonResponse(response, status=HTTPStatus.OK)


# @method_decorator(csrf_exempt, name='dispatch')
# class TicketObjectForSubTasksInStandardTicketApiEventVersion1Component(View):
#
#     def post(self, *args, **kwargs):
#         projectId = self.request.POST.get("project-id", None)
#         ticketSummary = self.request.POST.get("ticket-summary", None)
#         standardTicketId = self.request.POST.get("ticket-id", None)
#
#         ticketIssueTypeComponents = cache.get("ticketIssueTypeComponents")
#         ticketSecurityComponents = cache.get("ticketSecurityComponents")
#         ticketPriorityComponents = cache.get("ticketPriorityComponents")
#
#         project = Project.object.get(id=projectId)
#         newTicketNumber = project.projectTickets.count() + 1
#
#         ticket = Ticket()
#         ticket.internalKey = project.code + "-" + str(newTicketNumber)
#         ticket.summary = ticketSummary
#         ticket.project = project
#         ticket.reporter = self.request.user
#         ticket.issueType = next((i for i in ticketIssueTypeComponents if i.code == "SUB_TASK"), None)
#         ticket.securityLevel = next((i for i in ticketSecurityComponents if i.code == "INTERNAL"), None)
#         ticket.priority = next((i for i in ticketPriorityComponents if i.code == "MEDIUM"), None)
#
#         if standardTicketId is not None:
#             standardTicket = Ticket.object.get(id=standardTicketId)
#             ticket.sprint = standardTicket.sprint
#             ticket.status = standardTicket.status
#             ticket.board = standardTicket.board
#             ticket.column = standardTicket.column
#
#             ticket.save()
#             standardTicket.subTask.add(ticket)
#
#             response = {
#                 "success": True,
#                 "data": {
#                     "id": ticket.id,
#                     "internalKey": ticket.internalKey,
#                     "summary": ticket.summary,
#                     "link": "/jira2/ticket/" + str(ticket.internalKey),
#                     "issueType": {
#                         "internalKey": ticket.issueType.internalKey,
#                         "icon": "/static/" + ticket.issueType.icon,
#                     },
#                     "priority": {
#                         "internalKey": ticket.priority.internalKey,
#                         "icon": "/static/" + ticket.priority.icon
#                     },
#                 }
#             }
#             return JsonResponse(response, status=HTTPStatus.OK)
#
#         response = {
#             "success": False,
#             "message": "Unable to create a subtask."
#         }
#         return JsonResponse(response, status=HTTPStatus.BAD_REQUEST)
#
#
# @method_decorator(csrf_exempt, name='dispatch')
# class TicketObjectBaseDataUpdateApiEventVersion1Component(View):
#
#     def put(self, *args, **kwargs):
#         ticketId = self.kwargs.get("ticketId", None)
#         put = QueryDict(self.request.body)
#
#         try:
#             ticket = Ticket.object.get(id=ticketId)
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
#         project = Project.object.get(id=projectId)
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
#             epicTicket = Ticket.object.get(id=epicTicketId, issueType__code="EPIC")
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
# @method_decorator(csrf_exempt, name='dispatch')
# class KanbanBoardDetailsAndItemsApiEventVersion1Component(View):
#
#     def get(self, *args, **kwargs):
#         boardId = self.kwargs.get("boardId", None)
#
#         try:
#             board = Board.object.get(id=boardId)
#         except Board.DoesNotExist:
#             response = {
#                 "success": False,
#                 "message": "Could not find a board for id: " + str(boardId)
#             }
#             return JsonResponse(response, status=HTTPStatus.NOT_FOUND)
#
#         backLogColumn = Column.object.filter(board=board, name__icontains="BACKLOG").first()
#         otherColumns = Column.object.filter(board=board).exclude(id=backLogColumn.id).prefetch_related('columnTickets')
#
#         response = {
#             "success": True,
#             "data": {
#                 "board": {
#                     "id": board.id,
#                     "name": board.name,
#                 },
#                 # "sprint": {
#                 #     "id": board.sprint.id,
#                 #     "internalKey": board.sprint.internalKey,
#                 #     "remainingDays": (board.sprint.endDate - datetime.today().date()).days
#                 # },
#                 "members": [
#                     {
#                         "id": i.pk,
#                         "firstName": i.first_name,
#                         "lastName": i.last_name,
#                         "icon": i.developerProfile.profilePicture.url
#                     }
#                     for i in board.members.all()
#                 ],
#                 "columns": [
#                     {
#                         "id": i.id,
#                         "name": i.name,
#                         "tickets": serializeTicketsIntoChunks(i.columnTickets.filter(~Q(issueType__code="EPIC")))
#                     }
#                     for i in otherColumns
#                 ]
#             }
#         }
#         return JsonResponse(response, status=HTTPStatus.OK)
#
#
# @method_decorator(csrf_exempt, name='dispatch')
# class KanbanBoardTicketColumnUpdateApiEventVersion1Component(View):
#
#     def put(self, *args, **kwargs):
#         put = QueryDict(self.request.body)
#
#         columnId = put.get("column-id")
#         ticketId = put.get("ticket-id")
#
#         Ticket.object.filter(id=ticketId).update(column_id=columnId)
#         # TODO: Need to update the ticket status.
#
#         response = {
#             "success": True,
#         }
#         return JsonResponse(response, status=HTTPStatus.OK)
#
#
# @method_decorator(csrf_exempt, name='dispatch')
# class KanbanBoardBacklogActiveTicketsApiEventVersion1Component(View):
#
#     def get(self, *args, **kwargs):
#         boardId = self.kwargs.get("boardId", None)
#
#         try:
#             board = Board.object.get(id=boardId)
#         except Board.DoesNotExist:
#             response = {
#                 "success": False,
#                 "message": "Could not find a board for id: " + str(boardId)
#             }
#             return JsonResponse(response, status=HTTPStatus.NOT_FOUND)
#
#         backLogColumn = Column.object.filter(board=board, name__icontains="BACKLOG").first()
#         otherColumns = Column.object.filter(board=board).exclude(id=backLogColumn.id)
#         otherColumnTickets = Ticket.object.filter(column__in=otherColumns,
#                                                   modifiedDttm__gte=datetime.now() - timedelta(days=7))
#
#         if not otherColumns.exists():
#             response = {
#                 "success": False,
#                 "message": "Unable to find active tickets."
#             }
#             return JsonResponse(response, status=HTTPStatus.NOT_FOUND)
#
#         response = {
#             "success": True,
#             "data": {
#                 "tickets": serializeTicketsIntoChunks(otherColumnTickets),
#                 "columns": {
#                     "inActive": {
#                         "id": backLogColumn.id,
#                     },
#                     "active": {
#                         "id": otherColumns.first().id
#                     }
#                 }
#             }
#         }
#         return JsonResponse(response, status=HTTPStatus.OK)
#
#
# @method_decorator(csrf_exempt, name='dispatch')
# class KanbanBoardBacklogActiveTicketsApiEventVersion2Component(View):
#
#     def get(self, *args, **kwargs):
#         boardId = self.kwargs.get("boardId", None)
#
#         try:
#             board = Board.object.get(id=boardId)
#         except Board.DoesNotExist:
#             response = {
#                 "success": False,
#                 "message": "Could not find a board for id: " + str(boardId)
#             }
#             return JsonResponse(response, status=HTTPStatus.NOT_FOUND)
#
#         backLogColumn = Column.object.filter(board=board, name__icontains="BACKLOG").first()
#         otherColumns = Column.object.filter(board=board).exclude(id=backLogColumn.id)
#         otherColumnTickets = Ticket.object.filter(column__in=otherColumns,
#                                                   modifiedDttm__gte=datetime.now() - timedelta(days=7))
#
#         if not otherColumns.exists():
#             response = {
#                 "success": False,
#                 "message": "Unable to find active tickets."
#             }
#             return JsonResponse(response, status=HTTPStatus.NOT_FOUND)
#
#         response = {
#             "success": True,
#             "data": {
#                 "tickets": serializeTicketsIntoChunks(otherColumnTickets.filter(~Q(issueType__code="EPIC"))),
#                 "columns": {
#                     "inActive": {
#                         "id": backLogColumn.id,
#                     },
#                     "active": {
#                         "id": otherColumns.first().id
#                     }
#                 }
#             }
#         }
#         return JsonResponse(response, status=HTTPStatus.OK)
#
#
# @method_decorator(csrf_exempt, name='dispatch')
# class KanbanBoardBacklogInActiveTicketsApiEventVersion1Component(View):
#
#     def get(self, *args, **kwargs):
#         boardId = self.kwargs.get("boardId", None)
#
#         try:
#             board = Board.object.get(id=boardId)
#         except Board.DoesNotExist:
#             response = {
#                 "success": False,
#                 "message": "Could not find a board for id: " + str(boardId)
#             }
#             return JsonResponse(response, status=HTTPStatus.NOT_FOUND)
#
#         backLogColumn = Column.object.filter(board=board, name__icontains="BACKLOG").first()
#         todoColumn = Column.object.filter(board=board, name__icontains="TO DO").first()
#
#         if backLogColumn is None or todoColumn is None:
#             response = {
#                 "success": False,
#                 "message": "Could not find a backlog for this board. Check the board settings."
#             }
#             return JsonResponse(response, status=HTTPStatus.NOT_FOUND)
#
#         response = {
#             "success": True,
#             "data": {
#                 "tickets": serializeTicketsIntoChunks(backLogColumn.columnTickets.all()),
#                 "columns": {
#                     "inActive": {
#                         "id": backLogColumn.id,
#                     },
#                     "active": {
#                         "id": todoColumn.id
#                     }
#                 }
#             }
#         }
#         return JsonResponse(response, status=HTTPStatus.OK)
#
#
# @method_decorator(csrf_exempt, name='dispatch')
# class KanbanBoardBacklogInActiveTicketsApiEventVersion2Component(View):
#
#     def get(self, *args, **kwargs):
#         boardId = self.kwargs.get("boardId", None)
#
#         try:
#             board = Board.object.get(id=boardId)
#         except Board.DoesNotExist:
#             response = {
#                 "success": False,
#                 "message": "Could not find a board for id: " + str(boardId)
#             }
#             return JsonResponse(response, status=HTTPStatus.NOT_FOUND)
#
#         backlogColumn = Column.object.filter(board=board, name__icontains="BACKLOG").first()
#         todoColumn = Column.object.filter(board=board, name__icontains="TO DO").first()
#
#         if backlogColumn is None or todoColumn is None:
#             response = {
#                 "success": False,
#                 "message": "Could not find a backlog for this board. Check the board settings."
#             }
#             return JsonResponse(response, status=HTTPStatus.NOT_FOUND)
#
#         response = {
#             "success": True,
#             "data": {
#                 "tickets": serializeTicketsIntoChunks(backlogColumn.columnTickets.filter(~Q(issueType__code="EPIC"))),
#                 "columns": {
#                     "inActive": {
#                         "id": backlogColumn.id,
#                     },
#                     "active": {
#                         "id": todoColumn.id
#                     }
#                 }
#             }
#         }
#         return JsonResponse(response, status=HTTPStatus.OK)
#
#
# @method_decorator(csrf_exempt, name='dispatch')
# class BoardObjectDetailsApiEventVersion1Component(View):
#
#     def get(self, *args, **kwargs):
#         boardId = self.kwargs.get("boardId", None)
#
#         try:
#             board = Board.object.get(id=boardId)
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
# @method_decorator(csrf_exempt, name='dispatch')
# class TicketObjectBulkCreateApiEventVersion1Component(View):
#
#     def post(self, *args, **kwargs):
#         body = json.loads(self.request.body)
#
#         for ticket in body['data']['tickets']:
#             project = Project.object.filter(code__icontains=ticket['projectCode']).first()
#
#             if project is None or Ticket.object.filter(internalKey=ticket["internalKey"]).exists():
#                 continue
#
#             newTicket = Ticket()
#             newTicket.internalKey = project.code + "-" + str(project.projectTickets.count() + 1)
#             newTicket.summary = ticket["summary"]
#             newTicket.description = ticket["description"]
#             newTicket.project = project
#             newTicket.reporter = User.object.get(username="admin")
#             newTicket.storyPoints = int(ticket["storyPoints"])
#             newTicket.issueType = Component.object.filter(componentGroup__code="TICKET_ISSUE_TYPE",
#                                                           internalKey=ticket["issueType"]).first()
#             newTicket.priority = Component.object.filter(componentGroup__code="TICKET_PRIORITY",
#                                                          internalKey=ticket["priority"]).first()
#             newTicket.board = project.boardProjects.first()
#             newTicket.column = project.boardProjects.first().boardColumns.first()
#             newTicket.save()
#         return JsonResponse({}, status=HTTPStatus.OK)
#
#
# def serializeTickets(tickets, data):
#     newData = [
#         {
#             "id": ticket.id,
#             "summary": ticket.summary,
#             "internalKey": ticket.internalKey,
#             "link": "/jira2/ticket/" + str(ticket.internalKey),
#             "storyPoints": ticket.storyPoints if ticket.storyPoints is not None else "-",
#             "column": ticket.column.name if ticket.column is not None else None,
#             "issueType": {
#                 "internalKey": ticket.issueType.internalKey,
#                 "icon": "/static/" + ticket.issueType.icon,
#             },
#             "priority": {
#                 "internalKey": ticket.priority.internalKey,
#                 "icon": "/static/" + ticket.priority.icon
#             },
#             "epic": {
#                 "id": ticket.epic.id,
#                 "internalKey": ticket.epic.internalKey,
#                 "summary": ticket.epic.summary,
#                 "colour": ticket.epic.colour,
#                 "link": "/jira2/ticket/" + str(ticket.epic.internalKey),
#             } if ticket.epic is not None else None,
#             "assignee": {
#                 "id": ticket.assignee.pk,
#                 "firstName": ticket.assignee.first_name,
#                 "lastName": ticket.assignee.last_name,
#                 "icon": ""  # ticket.assignee.developerProfile.profilePicture.url
#             } if ticket.assignee is not None else None,
#         }
#         for ticket in tickets
#     ]
#
#     for i in newData:
#         data.append(i)
#
#     return
#
#
# def serializeTicketsIntoChunks(tickets):
#     if tickets.count() == 0:
#         return []
#
#     data = []
#     JOBS = []
#     MAX_THREADS = 4
#     chunkSize = tickets.count() // MAX_THREADS
#
#     if chunkSize == 0:
#         serializeTickets(tickets, data)
#         return data
#
#     ticketsChunks = [tickets[i:i + chunkSize] for i in range(0, len(tickets), chunkSize)]
#
#     for index in ticketsChunks:
#         JOBS.append(threading.Thread(target=serializeTickets, args=(index, data,)))
#
#     for j in JOBS:
#         j.start()
#
#     for j in JOBS:
#         j.join()
#
#     return data