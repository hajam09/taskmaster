import json

from django.urls import reverse

from jira.models import Board
from taskmaster.operations import bakerOperations
from taskmaster.tests.BaseTestAjax import BaseTestAjax


class BoardObjectApiEventVersion2ComponentTest(BaseTestAjax):

    def setUp(self, path=reverse('jira:boardObjectApiEventVersion2Component')) -> None:
        self.basePath = path
        super(BoardObjectApiEventVersion2ComponentTest, self).setUp(self.basePath)

    def testGetBoardsEmptyList(self):
        response = self.get()
        ajaxResponse = json.loads(response.content)

        self.assertTrue(ajaxResponse["success"])
        self.assertEqual(0, len(ajaxResponse["data"]["boards"]))

    def testGetSpecificBoard(self):
        testParams = self.TestParams().createBoards('Board 1', True)
        response = self.get(path=self.basePath + f'?id={testParams.boards[0].id}')
        ajaxResponse = json.loads(response.content)
        self.assertTrue(ajaxResponse["success"])
        self.assertEqual(1, len(ajaxResponse["data"]["boards"]))

        for profile in ajaxResponse["data"]["boards"]:
            self.assertEqual(testParams.boards[0].id, profile['id'])
            self.assertEqual(testParams.boards[0].internalKey, profile['internalKey'])
            self.assertEqual(testParams.boards[0].url, profile['url'])
            self.assertEqual(testParams.boards[0].Types.SCRUM, profile['type'])
            self.assertIn('link', profile)

    def testGetAllBoards(self):
        testParams = self.TestParams().createBoards('Board 1', True).createBoards('Board 2', False)
        response = self.get(path=self.basePath)
        ajaxResponse = json.loads(response.content)

        self.assertTrue(ajaxResponse["success"])
        self.assertEqual(Board.objects.count(), len(ajaxResponse["data"]["boards"]))
        self.assertEqual([i.serializeBoardVersion1() for i in testParams.boards], ajaxResponse["data"]["boards"])

    class TestParams:
        def __init__(self):
            self.boards = []

        def createBoards(self, name, isScrum):
            boardType = Board.Types.SCRUM if isScrum else Board.Types.KANBAN
            self.boards.append(bakerOperations.createBoard(boardType, name))
            return self
