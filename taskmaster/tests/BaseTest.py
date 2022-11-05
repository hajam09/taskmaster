from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import Client
from django.test import RequestFactory
from django.test import TestCase

from taskmaster.operations import seedDataOperations, generalOperations
from taskmaster.settings import TEST_PASSWORD
from taskmaster.tests import userDataHelper


class BaseTest(TestCase):
    # coverage run --source='.' manage.py test && coverage html

    def setUp(self, url='') -> None:
        """
        setUp: Run once for every test method to setup clean data.
        """
        self.factory = RequestFactory()
        self.user = userDataHelper.createNewUser()
        self.client = Client(
            HTTP_USER_AGENT='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'
        )

        self.request = self.factory.get(url)
        self.request.user = self.user

        self.client.login(username=self.user.username, password=TEST_PASSWORD)

        # To fix the messages during unit testing
        setattr(self.request, 'session', 'session')
        messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', messages)

    @classmethod
    def setUpClass(cls):
        seedDataOperations.runSeedDataInstaller()
        generalOperations.setCaches()
        super(BaseTest, cls).setUpClass()

    def tearDown(self) -> None:
        self.client.logout()
        self.user.delete()
        super(BaseTest, self).tearDown()

    @classmethod
    def tearDownClass(cls):
        super(BaseTest, cls).tearDownClass()

    @classmethod
    def setUpTestData(cls):
        """
        setUpTestData: Run once to set up non-modified data for all class methods.
        """
        pass

    def getSessionKey(self):
        return self.client.session.session_key

    def getMessages(self, response):
        return list(get_messages(response.wsgi_request))
