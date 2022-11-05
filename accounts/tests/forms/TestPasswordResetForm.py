from accounts.forms import PasswordResetForm
from taskmaster.tests.BaseTest import BaseTest


class PasswordResetFormTest(BaseTest):
    def setUp(self, path='') -> None:
        self.basePath = path
        super(PasswordResetFormTest, self).setUp('')
        self.client.logout()

    def testNewPasswordAndConfirmPasswordNotEqual(self):
        testParams = self.TestParams('RaNdOmPaSsWoRd56', 'RaNdOmPaSsWoRd65')
        form = PasswordResetForm(request=self.request, user=self.user, data=testParams.getData())
        self.assertFalse(form.is_valid())

        for message in form.errors.as_data().get('__all__')[0]:
            self.assertEquals(message, 'Your new password and confirm password does not match.')

    def testNewPasswordNotStrongEnough(self):
        testParams = self.TestParams('123', '123')
        form = PasswordResetForm(request=self.request, user=self.user, data=testParams.getData())
        self.assertFalse(form.is_valid())

        for message in form.errors.as_data().get('__all__')[0]:
            self.assertEquals(message, 'Your new password is not strong enough.')

    def testPasswordResetSuccessful(self):
        testParams = self.TestParams('RaNdOmPaSsWoRd56', 'RaNdOmPaSsWoRd56')
        form = PasswordResetForm(request=self.request, user=self.user, data=testParams.getData())
        self.assertTrue(form.is_valid())
        form.updatePassword()

        self.assertTrue(self.request.user.check_password('RaNdOmPaSsWoRd56'))

    class TestParams:
        def __init__(self, password, repeatPassword):
            self.password = password
            self.repeatPassword = repeatPassword

        def getData(self):
            data = {
                'password': self.password,
                'repeatPassword': self.repeatPassword,
            }
            return data
