from unittest.mock import patch

from django.core.cache import cache
from django.urls import reverse

from taskmaster.settings import TEST_PASSWORD
from taskmaster.tests.BaseTestViews import BaseTestViews


class AccountsLoginViewTest(BaseTestViews):

    def setUp(self, path=reverse('accounts:login')) -> None:
        self.basePath = path
        super(AccountsLoginViewTest, self).setUp(self.basePath)
        self.client.logout()

    def testLoginGet(self):
        response = self.get()
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')

    @patch('accounts.views.LoginForm.is_valid')
    def testLoginAuthenticateValidUser(self, mockLoginForm):
        mockLoginForm.return_value = True
        testParams = self.TestParams(self.user.email, TEST_PASSWORD)
        self.client.login(username=self.user.username, password=TEST_PASSWORD)

        response = self.post(testParams.getData())
        sessionKey = self.getSessionKey()

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, '/dashboard/')
        self.assertIn('_auth_user_id', self.client.session)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)
        self.assertEqual(cache.get(sessionKey), None)

    @patch('accounts.views.LoginForm.is_valid')
    def testLoginAuthenticateInvalidUser(self, mockLoginForm):
        mockLoginForm.return_value = False
        testParams = self.TestParams(self.user.username, 'TEST_PASSWORD')
        response = self.post(testParams.getData())
        sessionKey = self.getSessionKey()

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")
        self.assertNotIn('_auth_user_id', self.client.session)

        self.assertEqual(cache.get(sessionKey), 1)

    def testLoginMaxAttempts(self):
        response = None
        for i in range(6):
            response = self.post()

        self.assertNotEqual(cache.get(self.getSessionKey()), None)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, '/accounts/login/')

        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)

        for message in messages:
            self.assertEqual(
                str(message),
                'Your account has been temporarily locked out because of too many failed login attempts.'
            )
        cache.set(self.getSessionKey(), None)

    class TestParams:

        def __init__(self, email, password):
            self.email = email
            self.password = password

        def getData(self):
            data = {
                'email': self.email,
                'password': self.password,
            }
            return data
