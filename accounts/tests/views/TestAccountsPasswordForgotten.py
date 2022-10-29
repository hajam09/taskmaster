from unittest.mock import patch

from django.urls import reverse

from taskmaster.tests.BaseTestViews import BaseTestViews


class AccountsPasswordForgottenTest(BaseTestViews):

    def setUp(self, path=reverse('accounts:password-forgotten')) -> None:
        self.basePath = path
        super(AccountsPasswordForgottenTest, self).setUp(self.basePath)
        self.client.logout()

    def testLoginGet(self):
        response = self.get()
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/passwordForgotten.html')

    @patch('taskmaster.operations.emailOperations.sendEmailToResetPassword')
    def testPasswordRequestExistingUser(self, mockSendEmailToResetPassword):
        testParams = self.TestParams(self.user.email)
        response = self.post(testParams.getData())
        messages = self.getMessages(response)

        for message in messages:
            self.assertEqual(
                str(message),
                'Check your email for a password change link.'
            )

        mockSendEmailToResetPassword.assert_called_once()

    @patch('taskmaster.operations.emailOperations.sendEmailToResetPassword')
    def testPasswordRequestNonExistingUser(self, mockSendEmailToResetPassword):
        testParams = self.TestParams("example@example.com")
        response = self.post(testParams.getData())
        messages = self.getMessages(response)

        for message in messages:
            self.assertEqual(
                str(message),
                'Check your email for a password change link.'
            )

        mockSendEmailToResetPassword.assert_not_called()

    class TestParams:

        def __init__(self, email):
            self.email = email

        def getData(self):
            data = {
                'email': self.email,
            }
            return data
