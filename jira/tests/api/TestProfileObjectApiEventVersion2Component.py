import json

from django.core.cache import cache
from django.db.models import F
from django.urls import reverse

from accounts.models import Profile
from taskmaster.operations import databaseOperations, bakerOperations
from taskmaster.tests.BaseTestAjax import BaseTestAjax


class ProfileObjectApiEventVersion2ComponentTest(BaseTestAjax):

    def setUp(self, path=reverse('jira:profileObjectApiEventVersion2Component')) -> None:
        self.basePath = path
        self.bugIssueType = databaseOperations.getObjectByCode(cache.get('TICKET_ISSUE_TYPE'), 'BUG')
        super(ProfileObjectApiEventVersion2ComponentTest, self).setUp(self.basePath)

    def testGetProfilesEmptyList(self):
        response = self.get()
        ajaxResponse = json.loads(response.content)

        self.assertTrue(ajaxResponse["success"])
        self.assertEqual(0, len(ajaxResponse["data"]["profiles"]))

    def testGetSpecificProfile(self):
        users = bakerOperations.createUserObjects(6, 3)
        bakerOperations.createProfileObjects(users)
        firstProfile = Profile.objects.first()

        response = self.get(path=self.basePath + f'?user__id={firstProfile.user.id}')
        ajaxResponse = json.loads(response.content)
        self.assertTrue(ajaxResponse["success"])
        self.assertEqual(len(ajaxResponse["data"]["profiles"]), 1)

        for profile in ajaxResponse["data"]["profiles"]:
            self.assertEqual(firstProfile.id, profile['id'])
            self.assertEqual(firstProfile.user.first_name, profile['firstName'])
            self.assertEqual(firstProfile.user.last_name, profile['lastName'])

    def testGetAllProfiles(self):
        bakerOperations.createUserObjects(6, 3)
        bakerOperations.createProfileObjects()
        profiles = Profile.objects.annotate(
            pk=F('id'), firstName=F('user__first_name'), lastName=F('user__last_name')
        ).values('id', 'firstName', 'lastName')

        response = self.get()
        ajaxResponse = json.loads(response.content)

        self.assertTrue(ajaxResponse["success"])
        self.assertEqual(profiles.count(), len(ajaxResponse["data"]["profiles"]))
        self.assertEqual(list(profiles), ajaxResponse["data"]["profiles"])
