from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from taskmaster.operations import bakerOperations
from taskmaster.tests.BaseTestViews import BaseTestViews


class ActivateAccountViewTest(BaseTestViews):

    def setUp(self, path='') -> None:
        self.basePath = path
        self.prtg = PasswordResetTokenGenerator()
        super(ActivateAccountViewTest, self).setUp('')
        self.request.user.is_active = False
        self.request.user.save()
        self.client.logout()

    def testDjangoUnicodeDecodeErrorCaught(self):
        token = self.prtg.make_token(self.request.user)
        path = reverse('accounts:activate-account', kwargs={'encodedId': 'DECODE_ERROR', "token": token})
        response = self.get(path=path)
        self.assertTemplateUsed(response, 'accounts/activateFailed.html')

    def testUserDoesNotExistCaught(self):
        uid = urlsafe_base64_encode(force_bytes(0))
        token = self.prtg.make_token(self.request.user)
        path = reverse('accounts:activate-account', kwargs={'encodedId': uid, "token": token})
        response = self.get(path=path)
        self.assertTemplateUsed(response, 'accounts/activateFailed.html')

    def testValueErrorCaught(self):
        uid = urlsafe_base64_encode(force_bytes('ID'))
        token = self.prtg.make_token(self.request.user)
        path = reverse('accounts:activate-account', kwargs={'encodedId': uid, "token": token})
        response = self.get(path=path)
        self.assertTemplateUsed(response, 'accounts/activateFailed.html')

    def testIncorrectToken(self):
        newUser = bakerOperations.createUser()
        uid = urlsafe_base64_encode(force_bytes(newUser.id))
        token = self.prtg.make_token(self.request.user)
        path = reverse('accounts:activate-account', kwargs={'encodedId': uid, "token": token})
        response = self.get(path=path)
        self.assertTemplateUsed(response, 'accounts/activateFailed.html')

    def testUserActivatedSuccessfully(self):
        self.assertFalse(self.request.user.is_active)

        uid = urlsafe_base64_encode(force_bytes(self.request.user.id))
        token = self.prtg.make_token(self.request.user)
        path = reverse('accounts:activate-account', kwargs={'encodedId': uid, "token": token})

        response = self.get(path=path)
        messages = self.getMessages(response)
        self.request.user.refresh_from_db()

        self.assertTrue(self.request.user.is_active)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/accounts/login/')

        self.assertEqual(1, len(messages))
        for message in messages:
            self.assertEqual(
                str(message),
                'Account activated successfully'
            )