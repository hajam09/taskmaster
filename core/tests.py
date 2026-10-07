from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient

from core.models import Board, Column, ColumnStatus, Label, Project, Ticket, TicketComment


class TicketInlineUpdateApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='editor', password='password')
        self.project = self.create_project('Project One', 'ONE')
        self.status = self.create_status(self.project, 'To Do')
        self.ticket = Ticket.objects.create(
            url='ONE-1',
            summary='Initial summary',
            project=self.project,
            reporter=self.user,
            columnStatus=self.status,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.client.force_login(user=self.user)
        self.api_url = reverse('core:ticketApiVersion1')
        self.user_search_url = reverse('core:userLiveSearchApiVersion1')
        self.label_search_url = reverse('core:labelLiveSearchApiVersion1')
        self.ticket_search_url = reverse('core:ticketLiveSearchApiVersion1')
        self.ticket_page_url = reverse('core:ticket-view', kwargs={'url': self.ticket.url})
        self.comments_url = reverse('core:ticket-comments', kwargs={'ticket_id': self.ticket.id})
        self.subtasks_url = reverse('core:ticket-subtasks', kwargs={'ticket_id': self.ticket.id})

    @staticmethod
    def create_project(name, code):
        lead = User.objects.create_user(username=f'lead-{code}')
        return Project.objects.create(
            name=name,
            code=code,
            description='',
            lead=lead,
        )

    @staticmethod
    def create_status(project, name):
        board = Board.objects.create(name=f'{name} board {project.code}', project=project)
        column = Column.objects.create(name=name, board=board, status=Column.Status.TODO)
        return ColumnStatus.objects.create(name=name, column=column)

    def test_patch_updates_inline_ticket_fields_and_returns_updated_ticket(self):
        label = Label.objects.create(name='backend', colour=Label.Colour.BLUE)
        response = self.client.patch(
            self.api_url,
            {
                'summary': 'Updated summary',
                'description': 'Updated description',
                'storyPoints': 3,
                'type': Ticket.Type.BUG,
                'priority': Ticket.Priority.HIGH,
                'assignee': self.user.id,
                'columnStatus': self.status.id,
                'resolution': Ticket.Resolution.FIXED,
                'label': [label.id],
            },
            format='json',
            QUERY_STRING=f'url={self.ticket.url}',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['summary'], 'Updated summary')
        self.assertEqual(response.data['description'], 'Updated description')
        self.assertEqual(response.data['storyPoints'], 3)
        self.assertEqual(response.data['assignee']['id'], self.user.id)
        self.assertEqual(response.data['columnStatus']['id'], self.status.id)
        self.assertEqual(response.data['label'][0]['id'], label.id)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.summary, 'Updated summary')

    def test_patch_rejects_status_from_another_project(self):
        other_project = self.create_project('Project Two', 'TWO')
        other_status = self.create_status(other_project, 'In Progress')

        response = self.client.patch(
            self.api_url,
            {'columnStatus': other_status.id},
            format='json',
            QUERY_STRING=f'url={self.ticket.url}',
        )

        self.assertEqual(response.status_code, 400)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.columnStatus_id, self.status.id)

    def test_patch_rejects_status_from_another_board_in_same_project(self):
        other_status = self.create_status(self.project, 'In Progress')

        response = self.client.patch(
            self.api_url,
            {'columnStatus': other_status.id},
            format='json',
            QUERY_STRING=f'url={self.ticket.url}',
        )

        self.assertEqual(response.status_code, 400)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.columnStatus_id, self.status.id)

    def test_patch_accepts_status_from_same_board(self):
        second_status = ColumnStatus.objects.create(
            name='In Progress',
            column=self.status.column,
        )

        response = self.client.patch(
            self.api_url,
            {'columnStatus': second_status.id},
            format='json',
            QUERY_STRING=f'url={self.ticket.url}',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['columnStatus']['id'], second_status.id)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.columnStatus_id, second_status.id)

    def test_description_html_is_sanitized_before_saving(self):
        response = self.client.patch(
            self.api_url,
            {
                'description': (
                    '<p>Safe <strong>formatting</strong>'
                    '<script>alert("unsafe")</script>'
                    '<a href="javascript:alert(1)">bad link</a></p>'
                )
            },
            format='json',
            QUERY_STRING=f'url={self.ticket.url}',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('<strong>formatting</strong>', response.data['description'])
        self.assertNotIn('<script>', response.data['description'])
        self.assertNotIn('javascript:', response.data['description'])
        self.ticket.refresh_from_db()
        self.assertNotIn('<script>', self.ticket.description)

    def test_user_live_search_returns_matching_users(self):
        matching_user = User.objects.create_user(
            username='alexandra',
            first_name='Alexandra',
            last_name='Taylor',
        )
        User.objects.create_user(username='different', first_name='Morgan', last_name='Reed')

        response = self.client.get(self.user_search_url, {'query': 'alex'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            [{
                'id': matching_user.id,
                'name': 'Alexandra Taylor',
                'icon': 'https://cdn3.iconfinder.com/data/icons/avatars-round-flat/33/man5-512.png',
            }],
        )

    def test_user_live_search_returns_first_ten_users_without_query(self):
        for index in range(12):
            User.objects.create_user(
                username=f'user-{index:02}',
                first_name=f'User {index:02}',
            )

        response = self.client.get(self.user_search_url)
        expected_users = User.objects.order_by(
            'first_name', 'last_name', 'username'
        )[:10]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 10)
        self.assertEqual(
            [item['id'] for item in response.data],
            [user.id for user in expected_users],
        )

    def test_label_live_search_returns_matching_labels_with_colour(self):
        matching_label = Label.objects.create(name='backend', colour=Label.Colour.BLUE)
        Label.objects.create(name='frontend', colour=Label.Colour.GREEN)

        response = self.client.get(self.label_search_url, {'query': 'back'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            [{
                'id': matching_label.id,
                'name': matching_label.name,
                'colour': matching_label.colour,
            }],
        )

    def test_label_live_search_returns_first_ten_without_query(self):
        for index in range(12):
            Label.objects.create(
                name=f'label-{index:02}',
                colour=Label.Colour.BLUE,
            )

        response = self.client.get(self.label_search_url)
        expected_labels = Label.objects.order_by('name')[:10]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 10)
        self.assertEqual(
            [item['id'] for item in response.data],
            [label.id for label in expected_labels],
        )

    def test_ticket_live_search_returns_first_ten_without_query(self):
        tickets = [
            Ticket.objects.create(
                url=f'ONE-{index + 2}',
                summary=f'Issue {index}',
                project=self.project,
                reporter=self.user,
                columnStatus=self.status,
            )
            for index in range(12)
        ]

        response = self.client.get(self.ticket_search_url)
        expected_tickets = Ticket.objects.order_by('url')[:10]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 10)
        self.assertEqual(
            [item['id'] for item in response.data],
            [ticket.id for ticket in expected_tickets],
        )

    def test_subtask_live_search_returns_first_ten_subtasks_without_query(self):
        subtasks = [
            Ticket.objects.create(
                url=f'ONE-{index + 2}',
                summary=f'Subtask {index}',
                type=Ticket.Type.SUB_TASK,
                project=self.project,
                reporter=self.user,
                columnStatus=self.status,
            )
            for index in range(12)
        ]

        response = self.client.get(self.ticket_search_url, {'subTaskOnly': 'true'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 10)
        self.assertEqual(
            [item['id'] for item in response.data],
            [ticket.id for ticket in sorted(subtasks, key=lambda ticket: ticket.url)[:10]],
        )

    def test_ticket_subtasks_api_lists_only_the_parent_tickets_subtasks(self):
        subtask = Ticket.objects.create(
            url='ONE-2',
            summary='Implement API',
            type=Ticket.Type.SUB_TASK,
            project=self.project,
            reporter=self.user,
            columnStatus=self.status,
        )
        unrelated_subtask = Ticket.objects.create(
            url='ONE-3',
            summary='Unrelated',
            type=Ticket.Type.SUB_TASK,
            project=self.project,
            reporter=self.user,
            columnStatus=self.status,
        )
        self.ticket.subTask.add(subtask)

        response = self.client.get(self.subtasks_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['id'] for item in response.data], [subtask.id])
        self.assertNotIn(unrelated_subtask.id, [item['id'] for item in response.data])
        self.assertEqual(response.data[0]['href'], subtask.getUrl)

    def test_ticket_subtasks_api_creates_subtask_from_summary(self):
        response = self.client.post(
            self.subtasks_url,
            {'summary': 'New subtask'},
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        subtask = Ticket.objects.get(url='ONE-2')
        self.assertEqual(subtask.summary, 'New subtask')
        self.assertEqual(subtask.type, Ticket.Type.SUB_TASK)
        self.assertEqual(subtask.reporter, self.user)
        self.assertTrue(self.ticket.subTask.filter(id=subtask.id).exists())
        self.assertEqual(response.data['id'], subtask.id)

    def test_ticket_subtasks_api_attaches_existing_subtasks(self):
        subtask = Ticket.objects.create(
            url='ONE-2',
            summary='Existing subtask',
            type=Ticket.Type.SUB_TASK,
            project=self.project,
            reporter=self.user,
            columnStatus=self.status,
        )

        response = self.client.post(
            self.subtasks_url,
            {'ticket_ids': [subtask.id]},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['id'] for item in response.data], [subtask.id])
        self.assertTrue(self.ticket.subTask.filter(id=subtask.id).exists())

    def test_ticket_subtasks_api_rejects_non_subtasks(self):
        response = self.client.post(
            self.subtasks_url,
            {'ticket_ids': [self.ticket.id]},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(self.ticket.subTask.exists())

    def test_ticket_page_renders_subtasks_from_the_api(self):
        response = self.client.get(self.ticket_page_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="subtaskList"')
        self.assertNotContains(response, 'ticket.subTask.all')

    def test_comments_api_lists_comments_with_reaction_state(self):
        comment = TicketComment.objects.create(
            ticket=self.ticket,
            creator=self.user,
            comment='<p>Useful comment</p>',
        )
        comment.likes.add(self.user)

        response = self.client.get(self.comments_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], comment.id)
        self.assertTrue(response.data[0]['inLikes'])
        self.assertEqual(response.data[0]['likesCount'], 1)
        self.assertIn('createdDateTime', response.data[0])

    def test_comments_api_creates_sanitized_comment_for_signed_in_user(self):
        response = self.client.post(
            self.comments_url,
            {'comment': '<p>Useful <strong>comment</strong><script>unsafe()</script></p>'},
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertFalse(response.data['inLikes'])
        self.assertFalse(response.data['inDisLikes'])
        self.assertEqual(response.data['likesCount'], 0)
        self.assertEqual(response.data['disLikesCount'], 0)
        comment = TicketComment.objects.get(ticket=self.ticket)
        self.assertEqual(comment.creator, self.user)
        self.assertIn('<strong>comment</strong>', comment.comment)
        self.assertNotIn('<script>', comment.comment)

    def test_comments_api_rejects_empty_comments(self):
        response = self.client.post(
            self.comments_url,
            {'comment': '<p><br></p>'},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(TicketComment.objects.filter(ticket=self.ticket).exists())

    def test_comment_detail_api_allows_creator_to_edit_comment(self):
        comment = TicketComment.objects.create(
            ticket=self.ticket,
            creator=self.user,
            comment='<p>Original comment</p>',
        )
        detail_url = reverse(
            'core:ticket-comment-detail',
            kwargs={'ticket_id': self.ticket.id, 'pk': comment.id},
        )

        response = self.client.patch(
            detail_url,
            {'comment': '<p>Edited comment</p>'},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        comment.refresh_from_db()
        self.assertEqual(comment.comment, '<p>Edited comment</p>')
        self.assertTrue(comment.edited)

    def test_comment_detail_api_prevents_other_users_from_editing_comment(self):
        other_user = User.objects.create_user(username='comment-owner')
        comment = TicketComment.objects.create(
            ticket=self.ticket,
            creator=other_user,
            comment='<p>Owner comment</p>',
        )
        detail_url = reverse(
            'core:ticket-comment-detail',
            kwargs={'ticket_id': self.ticket.id, 'pk': comment.id},
        )

        response = self.client.patch(
            detail_url,
            {'comment': '<p>Attempted edit</p>'},
            format='json',
        )

        self.assertEqual(response.status_code, 403)
        comment.refresh_from_db()
        self.assertEqual(comment.comment, '<p>Owner comment</p>')

    def test_comment_api_does_not_expose_comments_from_other_tickets(self):
        other_ticket = Ticket.objects.create(
            url='ONE-OTHER',
            summary='Other ticket',
            project=self.project,
            reporter=self.user,
            columnStatus=self.status,
        )
        other_comment = TicketComment.objects.create(
            ticket=other_ticket,
            creator=self.user,
            comment='<p>Other ticket comment</p>',
        )
        detail_url = reverse(
            'core:ticket-comment-detail',
            kwargs={'ticket_id': self.ticket.id, 'pk': other_comment.id},
        )

        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, 404)

    def test_ticket_comment_like_toggles_and_removes_existing_dislike(self):
        comment = TicketComment.objects.create(
            ticket=self.ticket,
            creator=self.user,
            comment='<p>Comment</p>',
        )
        comment.dislikes.add(self.user)

        response = self.client.post(
            reverse(
                'core:ticket-comment-detail',
                kwargs={'ticket_id': self.ticket.id, 'pk': comment.id},
            ),
            {'reaction': 'like'},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['likesCount'], 1)
        self.assertEqual(response.data['disLikesCount'], 0)
        self.assertTrue(response.data['inLikes'])
        self.assertFalse(response.data['inDisLikes'])
        self.assertTrue(comment.likes.filter(id=self.user.id).exists())
        self.assertFalse(comment.dislikes.filter(id=self.user.id).exists())

        self.client.post(
            reverse(
                'core:ticket-comment-detail',
                kwargs={'ticket_id': self.ticket.id, 'pk': comment.id},
            ),
            {'reaction': 'like'},
            format='json',
        )
        self.assertFalse(comment.likes.filter(id=self.user.id).exists())

    def test_ticket_comment_dislike_toggles_and_removes_existing_like(self):
        comment = TicketComment.objects.create(
            ticket=self.ticket,
            creator=self.user,
            comment='<p>Comment</p>',
        )
        comment.likes.add(self.user)

        response = self.client.post(
            reverse(
                'core:ticket-comment-detail',
                kwargs={'ticket_id': self.ticket.id, 'pk': comment.id},
            ),
            {'reaction': 'dislike'},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['likesCount'], 0)
        self.assertEqual(response.data['disLikesCount'], 1)
        self.assertFalse(response.data['inLikes'])
        self.assertTrue(response.data['inDisLikes'])
        self.assertTrue(comment.dislikes.filter(id=self.user.id).exists())
        self.assertFalse(comment.likes.filter(id=self.user.id).exists())

    def test_comment_detail_api_rejects_invalid_reaction(self):
        comment = TicketComment.objects.create(
            ticket=self.ticket,
            creator=self.user,
            comment='<p>Comment</p>',
        )
        detail_url = reverse(
            'core:ticket-comment-detail',
            kwargs={'ticket_id': self.ticket.id, 'pk': comment.id},
        )

        response = self.client.post(detail_url, {'reaction': 'applaud'}, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertFalse(comment.likes.exists())
        self.assertFalse(comment.dislikes.exists())
