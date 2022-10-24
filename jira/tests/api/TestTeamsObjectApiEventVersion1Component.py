import json
from http import HTTPStatus

from django.urls import reverse

from accounts.models import Team
from taskmaster.tests.BaseTestAjax import BaseTestAjax


class TeamsObjectApiEventVersion1ComponentTest(BaseTestAjax):
    def setUp(self) -> None:
        super(TeamsObjectApiEventVersion1ComponentTest, self).setUp(
            reverse('jira:teamsObjectApiEventVersion1Component', kwargs={'teamId': 0}))

    def testTeamNotFound(self):
        response = self.delete()
        ajaxResponse = json.loads(response.content)

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertFalse(ajaxResponse["success"])
        self.assertEqual("Could not find a team with url/id: {}".format(0), ajaxResponse["message"])

    def testDeleteTeamSuccessfully(self):
        testParams = self.TestParams().createTeam()
        testParams.team.admins.add(self.user)

        self.path = reverse('jira:teamsObjectApiEventVersion1Component', kwargs={'teamId': testParams.team.id})

        response = self.delete()
        testParams.team.refresh_from_db()

        ajaxResponse = json.loads(response.content)
        self.assertTrue(testParams.team.deleteFl)
        self.assertTrue(ajaxResponse["success"])

        messages = self.getMessages(response)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Your team has been deleted successfully!')

    def testDeleteTeamWithInsufficientPermission(self):
        testParams = self.TestParams().createTeam()
        self.path = reverse('jira:teamsObjectApiEventVersion1Component', kwargs={'teamId': testParams.team.id})

        response = self.delete()
        testParams.team.refresh_from_db()

        ajaxResponse = json.loads(response.content)
        self.assertFalse(testParams.team.deleteFl)
        self.assertFalse(ajaxResponse["success"])
        self.assertEqual("You don't have the permission to complete this operation.", ajaxResponse["message"])

        messages = self.getMessages(response)
        self.assertEqual(len(messages), 0)

    class TestParams:

        def __init__(self):
            self.team = None

        def createTeam(self):
            team = Team()
            team.internalKey = "Test team"
            team.internalKey = "Test description"
            team.save()
            self.team = team
            return self

        def getData(self):
            data = {
                "teamId": self.team.id,
            }
            return data

        def getPayloadAsPutFormat(self):
            putData = [
                f"{k}={v}"
                for k, v in self.getData().items()
            ]
            return "&".join(putData)
