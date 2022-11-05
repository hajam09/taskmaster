from jira.forms import TeamForm
from taskmaster.operations import bakerOperations
from taskmaster.tests.BaseTest import BaseTest


class TeamFormTest(BaseTest):

    def setUp(self, path='') -> None:
        self.basePath = path
        super(TeamFormTest, self).setUp('')

    def testTeamWithInternalKeyAlreadyExists(self):
        team = bakerOperations.createTeamObjects([self.request.user])[0]
        testParams = self.TestParams(team.internalKey, 'description')
        form = TeamForm(request=self.request, data=testParams.getData())
        self.assertFalse(form.is_valid())

        self.assertEquals(form.errors.as_data()['name'][0].message,
                          f'Team with name {team.internalKey} already exists!')

    def testCreateNewTeam(self):
        pass
        # testParams = self.TestParams('New team name', 'description', members=[self.request.user])
        # form = TeamForm(request=self.request, data=testParams.getData())
        # form.fields['admins'].inital = [(1, 2)]
        # self.assertTrue(form.is_valid())
        # form.save()

    class TestParams:
        def __init__(self, name, description, isPrivate=True, admins=None, members=None):
            self.name = name
            self.description = description
            self.visibility = 'MEMBERS' if isPrivate else 'EVERYONE'
            self.admins = admins or []
            self.members = members or []

        def getData(self):
            data = {
                'name': self.name,
                'description': self.description,
                'visibility': self.visibility,
                'admins': self.admins,
                'members': self.members,
            }
            return data
