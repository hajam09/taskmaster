import json

from django.urls import reverse

from accounts.models import Team
from taskmaster.tests import userDataHelper
from taskmaster.tests.BaseTestAjax import BaseTestAjax


class TeamsViewApiEventVersion1ComponentTest(BaseTestAjax):

    def setUp(self, path=None) -> None:
        self.testParams = self.TestParams().createTeam()
        self.basePath = reverse('jira:teamsViewApiEventVersion1Component', kwargs={'teamId': 0})
        super(TeamsViewApiEventVersion1ComponentTest, self).setUp(self.basePath)

    def testLeaveTeamNotFound(self):
        response = self.put()
        ajaxResponse = json.loads(response.content)

        self.assertFalse(ajaxResponse["success"])
        self.assertEqual(ajaxResponse["message"], "Could not find a team with url/id: {}".format(0))

    def testLeaveTeam(self):
        self.testParams.team.members.add(self.user)
        self.testParams.team.admins.add(self.user)

        path = reverse('jira:teamsViewApiEventVersion1Component', kwargs={'teamId': self.testParams.team.id})
        response = self.put(path=path)

        self.assertFalse(self.user in self.testParams.team.members.all())
        self.assertFalse(self.user in self.testParams.team.admins.all())

    class TestParams:

        def __init__(self):
            self.team = None
            self.user = userDataHelper.createNewUser()

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
