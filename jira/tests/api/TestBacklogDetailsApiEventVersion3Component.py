import json

from django.urls import reverse
from faker import Faker

from jira.api import serializeTicketsVersion2
from jira.models import Board, Ticket, Sprint
from taskmaster.operations import bakerOperations
from taskmaster.tests.BaseTestAjax import BaseTestAjax


class BacklogDetailsApiEventVersion3ComponentTest(BaseTestAjax):
    def setUp(self, path=reverse('jira:backlogDetailsApiEventVersion3Component', kwargs={'boardId': 0})) -> None:
        self.basePath = path
        super(BacklogDetailsApiEventVersion3ComponentTest, self).setUp(self.basePath)

    def testBoardNotFound(self):
        response = self.get()
        ajaxResponse = json.loads(response.content)

        self.assertFalse(ajaxResponse["success"])
        self.assertEqual(ajaxResponse["message"], f"Could not find a board for id: 0")

    def testGetScrumBoardBacklogDetails(self):
        testParams = self.TestParams('Scrum Board', True)
        path = reverse('jira:backlogDetailsApiEventVersion3Component', kwargs={'boardId': testParams.board.id})
        faker = Faker()

        bulkTickets = []
        inSprintTicketInternalKeys = []
        backlogTicketInternalKeys = []
        for columnStatus in testParams.columnStatusList:
            t1 = bakerOperations.createTicket(columnStatus=columnStatus, project=testParams.project, save=False)
            t1.internalKey = faker.pystr_format()
            t2 = bakerOperations.createTicket(columnStatus=columnStatus, project=testParams.project, save=False)
            t2.internalKey = faker.pystr_format()
            bulkTickets.extend([t1, t2])

            if columnStatus.internalKey == 'OPEN' and columnStatus.column.internalKey == 'BACKLOG':
                backlogTicketInternalKeys.extend([t1.internalKey, t2.internalKey])
            else:
                inSprintTicketInternalKeys.extend([t1.internalKey, t2.internalKey])

        Ticket.objects.bulk_create(bulkTickets)
        allTickets = Ticket.objects.all().select_related(
            'assignee__profile', 'epic', 'issueType', 'priority', 'resolution', 'columnStatus')

        sprintTickets = [t for t in allTickets if t.internalKey in inSprintTicketInternalKeys]
        chunkSize = 3
        ticketsIntoChunks = [sprintTickets[i:i + chunkSize] for i in range(0, len(sprintTickets), chunkSize)]
        backlogTickets = [t for t in allTickets if t.internalKey in backlogTicketInternalKeys]

        sprintInternalKey = []
        for tickets in ticketsIntoChunks:
            sprintName = f'Sprint {faker.pystr_format()}'
            sprint = Sprint.objects.create(board=testParams.board, internalKey=sprintName)
            sprintInternalKey.append(sprintName)
            sprint.addTicketsToSprint(tickets)

        response = self.get(path=path)
        ajaxResponse = json.loads(response.content)
        backlogGroups = ajaxResponse["data"]["backlogGroups"]

        self.assertTrue(ajaxResponse["success"])
        self.assertEqual(len(ticketsIntoChunks) + 1, len(backlogGroups))

        # assert in scrum 1 group
        scrum1 = backlogGroups[0]
        self.assertEqual(1, scrum1['id'])
        self.assertIn(scrum1['internalKey'], sprintInternalKey)
        self.assertTrue(scrum1['isActive'])
        self.assertListEqual(serializeTicketsVersion2(ticketsIntoChunks[0]), scrum1['tickets'])

        # assert in scrum 2 group
        scrum2 = backlogGroups[1]
        self.assertEqual(2, scrum2['id'])
        self.assertIn(scrum2['internalKey'], sprintInternalKey)
        self.assertFalse(scrum2['isActive'])
        self.assertListEqual(serializeTicketsVersion2(ticketsIntoChunks[1]), scrum2['tickets'])

        # assert in backlog group
        backlogGroup = backlogGroups[2]
        self.assertEqual(0, backlogGroup['id'])
        self.assertIn('Backlog', backlogGroup['internalKey'])
        self.assertFalse(scrum2['isActive'])
        self.assertListEqual(serializeTicketsVersion2(backlogTickets), backlogGroup['tickets'])

    def testGetKanbanBoardBacklogDetails(self):
        testParams = self.TestParams('Kanban Board', False)
        path = reverse('jira:backlogDetailsApiEventVersion3Component', kwargs={'boardId': testParams.board.id})
        faker = Faker()

        bulkTickets = []
        developmentTicketInternalKeys = []
        backlogTicketsInternalKeys = []
        for columnStatus in testParams.columnStatusList:
            t1 = bakerOperations.createTicket(columnStatus=columnStatus, project=testParams.project, save=False)
            t1.internalKey = faker.pystr_format()
            t2 = bakerOperations.createTicket(columnStatus=columnStatus, project=testParams.project, save=False)
            t2.internalKey = faker.pystr_format()
            bulkTickets.extend([t1, t2])

            if columnStatus.internalKey == 'OPEN':
                backlogTicketsInternalKeys.extend([t1.internalKey, t2.internalKey])
            else:
                developmentTicketInternalKeys.extend([t1.internalKey, t2.internalKey])

        Ticket.objects.bulk_create(bulkTickets)

        allTickets = Ticket.objects.all().select_related(
            'assignee__profile', 'epic', 'issueType', 'priority', 'resolution', 'columnStatus')
        serializedDevelopmentTickets = serializeTicketsVersion2(
            [t for t in allTickets if t.internalKey in developmentTicketInternalKeys])
        serializedBacklogTickets = serializeTicketsVersion2(
            [t for t in allTickets if t.internalKey in backlogTicketsInternalKeys])

        response = self.get(path=path)
        ajaxResponse = json.loads(response.content)
        backlogGroups = ajaxResponse["data"]["backlogGroups"]

        self.assertTrue(ajaxResponse["success"])
        self.assertEqual(2, len(backlogGroups))

        # assert in development group
        developmentGroup = backlogGroups[0]
        self.assertEqual(1, developmentGroup['id'])
        self.assertEqual('In development', developmentGroup['internalKey'])
        self.assertTrue(developmentGroup['isActive'])
        self.assertEqual(len(developmentTicketInternalKeys), len(developmentGroup['tickets']))
        self.assertListEqual(serializedDevelopmentTickets, developmentGroup['tickets'])

        # assert in backlog group
        backlogGroup = backlogGroups[1]
        self.assertEqual(0, backlogGroup['id'])
        self.assertEqual('Backlog', backlogGroup['internalKey'])
        self.assertFalse(backlogGroup['isActive'])
        self.assertEqual(len(backlogTicketsInternalKeys), len(backlogGroup['tickets']))
        self.assertListEqual(serializedBacklogTickets, backlogGroup['tickets'])

    class TestParams:
        def __init__(self, name, isScrum):
            boardType = Board.Types.SCRUM if isScrum else Board.Types.KANBAN
            self.project = bakerOperations.createProject()
            self.board = bakerOperations.createBoard(boardType, name)
            self.columnList = bakerOperations.createColumns(self.board)
            self.columnStatusList = bakerOperations.createColumnStatus(self.board, self.columnList)
            self.profile = bakerOperations.createProfileObjects([self.project.lead])
