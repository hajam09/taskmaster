import json

from django.urls import reverse

from jira.models import Ticket
from taskmaster.operations import bakerOperations
from taskmaster.tests.BaseTestAjax import BaseTestAjax


class SubTaskTicketObjectForTicketApiEventVersion1ComponentTest(BaseTestAjax):

    def setUp(self, path=reverse('jira:subTaskTicketObjectForTicketApiEventVersion1Component')) -> None:
        self.basePath = path
        super(SubTaskTicketObjectForTicketApiEventVersion1ComponentTest, self).setUp(self.basePath)

    def testParentTicketNotFound(self):
        data = {
            'parentTicketId': 0,
            'summary': 'Test Summary'
        }
        response = self.post(data)
        ajaxResponse = json.loads(response.content)

        self.assertFalse(ajaxResponse["success"])
        self.assertEqual(ajaxResponse["message"], "Could not find a ticket with id: {}".format(data['parentTicketId']))

    def testCreateSubTaskSuccessfully(self):
        testParams = self.TestParams()
        payload = {
            'parentTicketId': testParams.ticket.id,
            'summary': 'Test Summary'
        }

        response = self.post(payload)
        ajaxResponse = json.loads(response.content)

        subTaskTicket = Ticket.objects.last()
        projectTicketCount = testParams.ticket.project.projectTickets.count()

        self.assertTrue(ajaxResponse["success"])
        self.assertEqual(f'{testParams.ticket.project.code}-{projectTicketCount}', subTaskTicket.internalKey)
        self.assertEqual(payload['summary'], subTaskTicket.summary)
        self.assertEqual('UNRESOLVED', subTaskTicket.resolution.code)
        self.assertEqual(testParams.ticket.project, subTaskTicket.project)
        self.assertEqual(self.request.user, subTaskTicket.reporter)
        self.assertEqual('SUB_TASK', subTaskTicket.issueType.code)
        self.assertEqual('MEDIUM', subTaskTicket.priority.code)
        self.assertEqual(testParams.ticket.columnStatus, subTaskTicket.columnStatus)
        self.assertEqual(projectTicketCount, subTaskTicket.orderNo)
        self.assertTrue(subTaskTicket in testParams.ticket.subTask.all())

        subTaskTicket.delete()

    class TestParams:

        def __init__(self):
            self.ticket = bakerOperations.createTicket()
