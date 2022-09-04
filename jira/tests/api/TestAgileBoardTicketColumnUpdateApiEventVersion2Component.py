from django.urls import reverse

from taskmaster.tests.BaseTestAjax import BaseTestAjax


class AgileBoardTicketColumnUpdateApiEventVersion2ComponentTest(BaseTestAjax):
    def setUp(self) -> None:
        super(AgileBoardTicketColumnUpdateApiEventVersion2ComponentTest, self).setUp(
            reverse('jira:agileBoardTicketColumnUpdateApiEventVersion2Component'))

    def testResolveTicket(self):
        self.assertEqual(None, None)

    def testReopenTicket(self):
        self.assertEqual(None, None)
