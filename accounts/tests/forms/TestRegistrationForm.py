from django.contrib.auth.models import User

from accounts.forms import RegistrationForm
from taskmaster.settings import TEST_PASSWORD
from taskmaster.tests.BaseTest import BaseTest


class RegistrationFormTest(BaseTest):
    def setUp(self, path='') -> None:
        self.basePath = path
        super(RegistrationFormTest, self).setUp('')
        self.client.logout()

    def testAccountAlreadyExists(self):
        testParams = self.TestParams(self.request.user.email, TEST_PASSWORD, TEST_PASSWORD)
        form = RegistrationForm(data=testParams.getData())
        self.assertFalse(form.is_valid())

        for message in form.errors.as_data()['email'][0]:
            self.assertEquals(message, 'An account already exists for this email address!')

    def testPasswordsNotEqual(self):
        testParams = self.TestParams('example@example.com', TEST_PASSWORD, 'TEST_PASSWORD')
        form = RegistrationForm(data=testParams.getData())
        self.assertFalse(form.is_valid())

        for message in form.errors.as_data()['password2'][0]:
            self.assertEquals(message, 'Your passwords do not match!')

    def testPasswordsNotStrong(self):
        testParams = self.TestParams('example@example.com', 'TEST_PASSWORD', 'TEST_PASSWORD')
        form = RegistrationForm(data=testParams.getData())
        self.assertFalse(form.is_valid())

        for message in form.errors.as_data()['password2'][0]:
            self.assertEquals(message, 'Your password is not strong enough.')

    def testRegisterUserSuccessfully(self):
        testParams = self.TestParams('example@example.com', TEST_PASSWORD, TEST_PASSWORD)
        form = RegistrationForm(data=testParams.getData())
        self.assertTrue(form.is_valid())
        form.save()

        user = User.objects.get(email='example@example.com')
        self.assertTrue(user.check_password(TEST_PASSWORD))
        self.assertEqual('firstName', user.first_name)
        self.assertEqual('lastName', user.last_name)

    class TestParams:
        def __init__(self, email, password1, password2):
            self.email = email
            self.password1 = password1
            self.password2 = password2
            self.firstName = 'firstName'
            self.lastName = 'lastName'

        def getData(self):
            data = {
                'email': self.email,
                'password1': self.password1,
                'password2': self.password2,
                'first_name': self.firstName,
                'last_name': self.lastName,
            }
            return data
