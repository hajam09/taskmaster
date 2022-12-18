from unittest.mock import patch

from django.http import QueryDict
from django.urls import reverse

from accounts.forms import RegistrationForm
from taskmaster.settings import TEST_PASSWORD
from taskmaster.tests.BaseTestViews import BaseTestViews


class AccountsRegisterViewTest(BaseTestViews):

    def setUp(self, path=reverse('accounts:register')) -> None:
        self.basePath = path
        super(AccountsRegisterViewTest, self).setUp(self.basePath)
        self.client.logout()

    def testRegisterGet(self):
        response = self.get()
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/registration.html')
        self.assertTrue(isinstance(response.context['form'], RegistrationForm))

    @patch('accounts.views.RegistrationForm.is_valid')
    @patch('accounts.views.RegistrationForm.save')
    @patch('taskmaster.operations.emailOperations.sendEmailToActivateAccount')
    def testLoginAuthenticateValidForm(self, mockRegistrationFormIsValid, mockRegistrationFormSave, mockSendEmailToActivateAccount):
        mockRegistrationFormIsValid.return_value = True
        mockRegistrationFormSave.save = self.request.user

        testParams = self.TestParams('user@example.com', TEST_PASSWORD, 'Django', 'Admin')
        response = self.post(testParams.getData())
        messages = self.getMessages(response)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(1, len(messages))
        mockSendEmailToActivateAccount.assert_called()
        self.assertRedirects(response, '/accounts/login/')

        for message in messages:
            self.assertEqual(
                str(message),
                'We\'ve sent you an activation link. Please check your email.'
            )

    class TestParams:
        def __init__(self, email, password, firstName, lastName):
            self.email = email
            self.password = password
            self.firstName = firstName
            self.lastName = lastName

        def getData(self):
            data = {
                'first_name': self.firstName,
                'last_name': self.lastName,
                'email': self.email,
                'password': self.password,

            }
            queryDict = QueryDict('', mutable=True)
            queryDict.update(data)
            return queryDict