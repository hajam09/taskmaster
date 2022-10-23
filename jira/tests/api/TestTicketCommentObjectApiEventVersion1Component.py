import json

from django.urls import reverse

from jira.models import TicketComment
from taskmaster.operations import bakerOperations
from taskmaster.tests import userDataHelper
from taskmaster.tests.BaseTestAjax import BaseTestAjax


class TicketCommentObjectApiEventVersion1ComponentTest(BaseTestAjax):

    def setUp(self, path=reverse('jira:ticketCommentObjectApiEventVersion1Component')) -> None:
        self.testParams = self.TestParams().createTicketComment()
        self.basePath = path
        super(TicketCommentObjectApiEventVersion1ComponentTest, self).setUp(self.basePath)
        bakerOperations.createProfileObjects([self.request.user])

    def testCreateTicketCommentUserNotAuthenticated(self):
        self.client.logout()
        payload = {
            'ticketId': self.testParams.ticket.id,
            'comment': 'updated comment'
        }

        response = self.post(payload)
        ajaxResponse = json.loads(response.content)

        self.assertFalse(ajaxResponse["success"])
        self.assertEquals(ajaxResponse["message"], "Please login to add a comment")

    def testCreateTicketCommentTicketDoesNotExist(self):
        payload = {
            'ticketId': '0',
            'comment': 'updated comment'
        }

        response = self.post(payload)
        ajaxResponse = json.loads(response.content)

        self.assertFalse(ajaxResponse["success"])
        self.assertEquals(ajaxResponse["message"], "Could not find a ticket with id: {}".format(payload['ticketId']))

    def testCreateTicketCommentSuccessfully(self):
        payload = {
            'ticketId': self.testParams.ticket.id,
            'comment': 'updated comment'
        }

        response = self.post(payload)
        ajaxResponse = json.loads(response.content)

        self.assertTrue(ajaxResponse["success"])
        self.assertEqual(2, TicketComment.objects.count())

        ticketComment = TicketComment.objects.filter(id=ajaxResponse["data"]["id"]).first()
        self.assertIsNotNone(ticketComment)
        self.assertEqual(self.testParams.ticket, ticketComment.ticket)
        self.assertEqual(self.user, ticketComment.creator)
        self.assertEqual(payload['comment'], ticketComment.comment)
        self.assertEqual(2, ticketComment.orderNo)

    def testDeleteTicketComment(self):
        payload = {
            'id': self.testParams.ticketComment.id,
        }

        response = self.delete(payload)
        ajaxResponse = json.loads(response.content)

        self.assertTrue(ajaxResponse["success"])
        self.assertFalse(TicketComment.objects.filter(id=payload['id']).exists())

    def testUpdateTicketComment(self):
        payload = {
            'id': self.testParams.ticketComment.id,
            'comment': 'new ticket comment',
        }

        response = self.put(payload)
        ajaxResponse = json.loads(response.content)
        self.testParams.ticketComment.refresh_from_db()

        self.assertTrue(ajaxResponse["success"])
        self.assertEqual(payload['comment'], self.testParams.ticketComment.comment)
        self.assertTrue(self.testParams.ticketComment.edited)



    class TestParams:

        def __init__(self):
            self.ticket = bakerOperations.createTicket(columnStatus=None, project=None)
            self.ticketComment = None
            self.user = userDataHelper.createNewUser()

        def createTicketComment(self):
            ticketComment = TicketComment()
            ticketComment.ticket = self.ticket
            ticketComment.creator = self.user
            ticketComment.comment = 'ticket comment'
            ticketComment.save()
            self.ticketComment = ticketComment
            return self
