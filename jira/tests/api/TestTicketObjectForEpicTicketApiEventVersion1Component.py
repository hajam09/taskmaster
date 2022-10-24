import json

from django.core.cache import cache
from django.urls import reverse

from jira.models import Ticket
from taskmaster.operations import bakerOperations, databaseOperations
from taskmaster.tests.BaseTestAjax import BaseTestAjax


class TicketObjectForEpicTicketApiEventVersion1ComponentTest(BaseTestAjax):

    def setUp(self, path=reverse('jira:ticketObjectForEpicTicketApiEventVersion1Component')) -> None:
        self.basePath = path
        self.bugIssueType = databaseOperations.getObjectByCode(cache.get('TICKET_ISSUE_TYPE'), 'BUG')
        super(TicketObjectForEpicTicketApiEventVersion1ComponentTest, self).setUp(self.basePath)

    def testCreateTicketForEpicTicketDoesNotExist(self):
        payload = {
            'ticketId': '0',
            'ticketSummary': 'Ticket Summary',
            'issueType': self.bugIssueType.id
        }

        response = self.post(payload)
        ajaxResponse = json.loads(response.content)

        self.assertFalse(ajaxResponse["success"])
        self.assertEqual(ajaxResponse["message"], "Could not find a ticket with id: {}".format(payload['ticketId']))

    def testCreateTicketForEpicTicketSuccessfully(self):
        testParams = self.TestParams()
        payload = {
            'ticketId': testParams.epicTicket.id,
            'ticketSummary': 'Ticket Summary',
            'issueType': self.bugIssueType.id
        }

        response = self.post(payload)
        ajaxResponse = json.loads(response.content)
        latestTicket = Ticket.objects.last()

        projectTicketCount = testParams.epicTicket.project.projectTickets.count()
        internalKey = f'{testParams.epicTicket.project.code}-{projectTicketCount}'
        unResolvedComponent = databaseOperations.getObjectByCode(cache.get('TICKET_RESOLUTIONS'), 'UNRESOLVED')
        priorityComponent = databaseOperations.getObjectByCode(cache.get('TICKET_PRIORITY'), 'MEDIUM')

        self.assertTrue(ajaxResponse["success"])
        self.assertEqual(internalKey, latestTicket.internalKey)
        self.assertEqual(payload['ticketSummary'], latestTicket.summary)
        self.assertEqual(unResolvedComponent, latestTicket.resolution)
        self.assertEqual(testParams.epicTicket.project, latestTicket.project)
        self.assertEqual(self.request.user, latestTicket.reporter)
        self.assertEqual(self.bugIssueType, latestTicket.issueType)
        self.assertEqual(priorityComponent, latestTicket.priority)
        self.assertEqual(testParams.epicTicket.columnStatus, latestTicket.columnStatus)
        self.assertEqual(testParams.epicTicket, latestTicket.epic)
        self.assertEqual(projectTicketCount, latestTicket.orderNo)
        latestTicket.delete()

    class TestParams:

        def __init__(self):
            self.issueType = databaseOperations.getObjectByCode(cache.get('TICKET_ISSUE_TYPE'), 'EPIC').id
            self.epicTicket = bakerOperations.createTicket(columnStatus=None, project=None, issueType=self.issueType)
