from django.urls import reverse

from jira.models import Board, Column, ColumnStatus, Sprint
from taskmaster.operations import bakerOperations
from taskmaster.tests.BaseTestViews import BaseTestViews


class JiraBoardsViewTest(BaseTestViews):

    def setUp(self, path=reverse('jira:boards-page')) -> None:
        self.basePath = path
        self.columnIndex = [
            ('BACKLOG', Column.Category.TODO, 1),
            ('TO DO', Column.Category.TODO, 2),
            ('IN PROGRESS', Column.Category.IN_PROGRESS, 3),
            ('DONE', Column.Category.DONE, 4),
        ]
        self.columnStatusIndex = [
            ('OPEN', ColumnStatus.Category.TODO),
            ('TO DO', ColumnStatus.Category.TODO),
            ('IN PROGRESS', ColumnStatus.Category.IN_PROGRESS),
            ('DONE', ColumnStatus.Category.DONE)
        ]
        super(JiraBoardsViewTest, self).setUp(self.basePath)

    def testLoginGet(self):
        response = self.get()
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'jira/boards.html')

    def assertObjects(self, payload, isKanban):
        createdBoard = Board.objects.get(internalKey__exact=payload['boardName'])
        columnList = Column.objects.filter(board=createdBoard)
        columnStatusList = ColumnStatus.objects.filter(board=createdBoard)

        self.assertEqual(4, columnList.count())

        for column, index in zip(columnList, self.columnIndex):
            self.assertEqual(index[0], column.internalKey)
            self.assertEqual(index[1], column.category)
            self.assertEqual(index[2], column.orderNo)

        self.assertEqual(4, columnStatusList.count())

        for status, column, index in zip(columnStatusList, columnList, self.columnStatusIndex):
            self.assertEqual(index[0], status.internalKey)
            self.assertEqual(column, status.column)
            self.assertEqual(index[1], status.category)

        sprintList = Sprint.objects.filter(board=createdBoard, isComplete=False)

        if isKanban:
            self.assertEqual(0, sprintList.count())
        else:
            self.assertEqual(1, sprintList.count())

            for i in sprintList:
                self.assertEqual(f'{createdBoard.internalKey} Sprint {1}', i.internalKey)
                self.assertEqual(1, i.orderNo)

        boardProjectIds = list(createdBoard.projects.values_list('id', flat=True))
        boardAdminIds = list(createdBoard.admins.values_list('id', flat=True))
        boardMemberIds = list(createdBoard.members.values_list('id', flat=True))

        self.assertListEqual(payload['boardProjects'], boardProjectIds)
        self.assertListEqual(payload['boardAdmins'], boardAdminIds)
        self.assertListEqual([], boardMemberIds)

    def testCreateKanbanBoardSuccessfully(self):
        testParams = self.TestParams(user=self.request.user, isKanban=True)
        response = self.post(testParams.payload)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, '/boards/')
        self.assertObjects(testParams.payload, isKanban=True)

    def testCreateScrumBoardSuccessfully(self):
        testParams = self.TestParams(user=self.request.user, isKanban=False)
        response = self.post(testParams.payload)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, '/boards/')
        self.assertObjects(testParams.payload, isKanban=False)

    def testCreateBoardWithExistingName(self):
        pass

    class TestParams:

        def __init__(self, user=None, numberOfProject=1, isKanban=True):
            self.projects = [bakerOperations.createProject(lead=user) for _ in range(numberOfProject)]
            self.boardType = Board.Types.KANBAN if isKanban else Board.Types.SCRUM
            self.payload = self.getData()

        def getData(self):
            data = {
                'boardName': 'Example Board Name',
                'boardType': self.boardType,
                'boardVisibility': 'visibility-members',
                'boardProjects': [p.id for p in self.projects],
                'boardAdmins': [p.lead.id for p in self.projects]
            }
            return data
