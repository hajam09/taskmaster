import json

from django.urls import reverse

from taskmaster.operations import bakerOperations
from taskmaster.tests.BaseTestAjax import BaseTestAjax


class UserDetailsApiEventVersion1ComponentTest(BaseTestAjax):

    def setUp(self, path=reverse('accounts:userDetailsApiEventVersion1Component')) -> None:
        self.basePath = path
        super(UserDetailsApiEventVersion1ComponentTest, self).setUp(self.basePath)
        self.userAndProfile = bakerOperations.createProfileObjects([self.request.user])

    def testGetUserAndProfileDetails(self):
        response = self.get()
        ajaxResponse = json.loads(response.content)

        self.assertTrue(ajaxResponse["success"])
        self.assertEqual(self.request.user.id, ajaxResponse["data"]["id"])
        self.assertEqual(self.request.user.email, ajaxResponse["data"]["email"])
        self.assertEqual(self.request.user.first_name, ajaxResponse["data"]["firstName"])
        self.assertEqual(self.request.user.last_name, ajaxResponse["data"]["lastName"])
        self.assertEqual(self.request.user.profile.publicName, ajaxResponse["data"]["publicName"])
        self.assertEqual(self.request.user.profile.jobTitle, ajaxResponse["data"]["jobTitle"])
        self.assertEqual(self.request.user.profile.department, ajaxResponse["data"]["department"])

    def testUpdateUserAndProfileDetails(self):
        payload = {
            "firstName": "Django",
            "lastName": "Admin",
            "publicName": "Django Admin",
            "jobTitle": "Dev Ops",
            "department": "IT Department",
        }

        response = self.put(payload)
        ajaxResponse = json.loads(response.content)

        self.assertTrue(ajaxResponse["success"])
        self.assertTrue(payload["firstName"], self.request.user.first_name)
        self.assertTrue(payload["lastName"], self.request.user.last_name)
        self.assertTrue(payload["publicName"], self.request.user.profile.publicName)
        self.assertTrue(payload["jobTitle"], self.request.user.profile.jobTitle)
        self.assertTrue(payload["department"], self.request.user.profile.department)
