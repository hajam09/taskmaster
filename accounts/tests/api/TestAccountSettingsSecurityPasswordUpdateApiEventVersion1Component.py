import json

from django.conf import settings
from django.urls import reverse

from taskmaster.tests.BaseTestAjax import BaseTestAjax


class AccountSettingsSecurityPasswordUpdateApiEventVersion1ComponentTest(BaseTestAjax):

    def setUp(self, path=reverse('accounts:accountSettingsSecurityPasswordUpdateApiEventVersion1Component')) -> None:
        self.basePath = path
        self.currentPasswordMessage = "Your current password does not match with the account\'s existing password."
        self.newPasswordMatchMessage = "Your new password and confirm password does not match."
        super(AccountSettingsSecurityPasswordUpdateApiEventVersion1ComponentTest, self).setUp(self.basePath)

    def testIncorrectCurrentPassword(self):
        payload = {
            'currentPassword': '123',
            'newPassword': '5!94@w5JbOdh',
            'repeatNewPassword': '5!94@w5JbOdh',
        }
        response = self.put(payload)
        ajaxResponse = json.loads(response.content)

        self.assertFalse(ajaxResponse["success"])
        self.assertEqual(1, len(ajaxResponse["data"]["errors"]))
        self.assertEqual(self.currentPasswordMessage, ajaxResponse["data"]["errors"][0])

    def testIncorrectNewPasswordAndRepeatNewPassword(self):
        payload = {
            'currentPassword': settings.TEST_PASSWORD,
            'newPassword': '5!94@w5JbOdh',
            'repeatNewPassword': 'cYL4e7R5H6q%',
        }

        response = self.put(payload)
        ajaxResponse = json.loads(response.content)

        self.assertFalse(ajaxResponse["success"])
        self.assertEqual(1, len(ajaxResponse["data"]["errors"]))
        self.assertEqual(self.newPasswordMatchMessage, ajaxResponse["data"]["errors"][0])

    def testIncorrectCurrentPasswordAndIncorrectNewPasswordAndRepeatNewPassword(self):
        payload = {
            'currentPassword': '123',
            'newPassword': '5!94@w5JbOdh',
            'repeatNewPassword': 'cYL4e7R5H6q%',
        }

        response = self.put(payload)
        ajaxResponse = json.loads(response.content)
        errorsList = ajaxResponse["data"]["errors"]

        self.assertFalse(ajaxResponse["success"])
        self.assertEqual(2, len(errorsList))
        self.assertListEqual([self.currentPasswordMessage, self.newPasswordMatchMessage], errorsList)

    def testUpdatePasswordSuccessfully(self):
        payload = {
            'currentPassword': settings.TEST_PASSWORD,
            'newPassword': '5!94@w5JbOdh',
            'repeatNewPassword': '5!94@w5JbOdh',
        }

        response = self.put(payload)
        ajaxResponse = json.loads(response.content)

        self.assertTrue(ajaxResponse["success"])
        self.request.user.check_password(payload['newPassword'])
        self.assertIn('_auth_user_id', self.client.session)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.request.user.pk)
