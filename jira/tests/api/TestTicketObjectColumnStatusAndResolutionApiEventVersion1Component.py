import json

from django.core.cache import cache
from django.urls import reverse

from taskmaster.operations import bakerOperations, databaseOperations
from taskmaster.tests.BaseTestAjax import BaseTestAjax


class TicketObjectColumnStatusAndResolutionApiEventVersion1ComponentTest(BaseTestAjax):
    def setUp(self, path=None) -> None:
        self.testParams = self.TestParams()
        self.resolutionList = cache.get('TICKET_RESOLUTIONS')
        self.basePath = reverse(
            'jira:ticketObjectColumnStatusAndResolutionApiEventVersion1Component',
            kwargs={'ticketId': self.testParams.ticket.id}
        )
        super(TicketObjectColumnStatusAndResolutionApiEventVersion1ComponentTest, self).setUp(self.basePath)

    def testCreateTicketForEpicTicketDoesNotExist(self):
        noTicketPath = self.basePath = reverse(
            'jira:ticketObjectColumnStatusAndResolutionApiEventVersion1Component', kwargs={'ticketId': 0}
        )
        response = self.put(path=noTicketPath)
        ajaxResponse = json.loads(response.content)

        self.assertFalse(ajaxResponse["success"])
        self.assertEqual(ajaxResponse["message"], "Could not find a ticket with id: {}".format(0))

    def testUpdateColumnStatusToInProgress(self):
        inProgressStatus = databaseOperations.getObjectByInternalKey(self.testParams.columnStatusList, "IN PROGRESS")
        unResolvedResolution = databaseOperations.getObjectByCode(self.resolutionList, "UNRESOLVED")

        payload = {
            'columnStatus': inProgressStatus.id
        }

        response = self.put(payload)
        self.testParams.ticket.refresh_from_db()
        ajaxResponse = json.loads(response.content)

        self.assertTrue(ajaxResponse["success"])
        self.assertEqual(inProgressStatus, self.testParams.ticket.columnStatus)
        self.assertEqual(unResolvedResolution, self.testParams.ticket.resolution)

    def testUpdateColumnStatusToDone(self):
        doneStatus = databaseOperations.getObjectByInternalKey(self.testParams.columnStatusList, "DONE")
        resolvedResolution = databaseOperations.getObjectByCode(self.resolutionList, "RESOLVED")

        payload = {
            'columnStatus': doneStatus.id
        }

        response = self.put(payload)
        self.testParams.ticket.refresh_from_db()
        ajaxResponse = json.loads(response.content)

        self.assertTrue(ajaxResponse["success"])
        self.assertEqual(doneStatus, self.testParams.ticket.columnStatus)
        self.assertEqual(resolvedResolution, self.testParams.ticket.resolution)

    def testUpdateColumnStatusDoneToInProgress(self):
        self.testUpdateColumnStatusToDone()

        inProgressStatus = databaseOperations.getObjectByInternalKey(self.testParams.columnStatusList, "IN PROGRESS")
        reOpenedResolution = databaseOperations.getObjectByCode(self.resolutionList, "REOPENED")

        payload = {
            'columnStatus': inProgressStatus.id
        }

        response = self.put(payload)
        self.testParams.ticket.refresh_from_db()
        ajaxResponse = json.loads(response.content)

        self.assertTrue(ajaxResponse["success"])
        self.assertEqual(inProgressStatus, self.testParams.ticket.columnStatus)
        self.assertEqual(reOpenedResolution, self.testParams.ticket.resolution)

    def testReOpenedToUnResolvedResolution(self):
        self.testUpdateColumnStatusDoneToInProgress()
        unResolvedResolution = databaseOperations.getObjectByCode(self.resolutionList, "UNRESOLVED")

        response = self.put()
        self.testParams.ticket.refresh_from_db()
        ajaxResponse = json.loads(response.content)

        self.assertTrue(ajaxResponse["success"])
        self.assertEqual(unResolvedResolution, self.testParams.ticket.resolution)

    class TestParams:

        def __init__(self):
            self.columnStatusList = bakerOperations.createColumnStatus()
            self.ticket = bakerOperations.createTicket(columnStatus=self.columnStatusList.first(), project=None)
