from accounts.forms import PasswordUpdateForm
from taskmaster.settings import TEST_PASSWORD
from taskmaster.tests.BaseTest import BaseTest


class PasswordUpdateFormTest(BaseTest):
    def setUp(self, path='') -> None:
        self.basePath = path
        super(PasswordUpdateFormTest, self).setUp('')

    def testIncorrectCurrentPassword(self):
        testParams = self.TestParams('TEST_PASSWORD', 'RaNdOmPaSsWoRd56', 'RaNdOmPaSsWoRd56')
        form = PasswordUpdateForm(request=self.request, data=testParams.getData())
        self.assertFalse(form.is_valid())

        for message in form.errors.as_data().get('__all__')[0]:
            self.assertEquals(message, 'Your current password does not match with the account\'s existing password.')

    def testNewAndConfirmPasswordNotEqual(self):
        testParams = self.TestParams(TEST_PASSWORD, 'RaNdOmPaSsWoRd56', 'RaNdOmPaSsWoRd65')
        form = PasswordUpdateForm(request=self.request, data=testParams.getData())
        self.assertFalse(form.is_valid())

        for message in form.errors.as_data().get('__all__')[0]:
            self.assertEquals(message, 'Your new password and confirm password does not match.')

    def testNewPasswordIsWeak(self):
        testParams = self.TestParams(TEST_PASSWORD, '123', '123')
        form = PasswordUpdateForm(request=self.request, data=testParams.getData())
        self.assertFalse(form.is_valid())

        for message in form.errors.as_data().get('__all__')[0]:
            self.assertEquals(message, 'Your new password is not strong enough.')

    def testUpdateNewPasswordSuccessfully(self):
        testParams = self.TestParams(TEST_PASSWORD, 'RaNdOmPaSsWoRd56', 'RaNdOmPaSsWoRd56')
        form = PasswordUpdateForm(request=self.request, data=testParams.getData())
        self.assertTrue(form.is_valid())
        form.updatePassword()

        self.assertTrue(self.request.user.check_password('RaNdOmPaSsWoRd56'))

    class TestParams:
        def __init__(self, currentPassword, newPassword, repeatNewPassword):
            self.currentPassword = currentPassword
            self.newPassword = newPassword
            self.repeatNewPassword = repeatNewPassword

        def getData(self):
            data = {
                'currentPassword': self.currentPassword,
                'newPassword': self.newPassword,
                'repeatNewPassword': self.repeatNewPassword,
            }
            return data
