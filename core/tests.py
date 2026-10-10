from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient

from core.models import Board, Column, ColumnStatus, Label, Project, Ticket, TicketComment, TicketLink


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
        self.api_url = reverse('ticket:ticketApiVersion1', kwargs={'ticketIdOrUrl': self.ticket.id})
        self.user_search_url = reverse('ticket:userLiveSearchApiVersion1')
        self.label_search_url = reverse('ticket:labelLiveSearchApiVersion1')
        self.ticket_search_url = reverse('ticket:ticketLiveSearchApiVersion1')
        self.ticket_page_url = reverse('ticket:ticket-view', kwargs={'url': self.ticket.url})
        self.comments_url = reverse('ticket:ticket-comments', kwargs={'ticketId': self.ticket.id})
        self.subtasks_url = reverse('ticket:ticket-subtasks', kwargs={'ticketIdOrUrl': self.ticket.id})
        self.epic_issues_url = reverse('ticket:ticket-epic-issues', kwargs={'ticketIdOrUrl': self.ticket.id})
        self.linked_issues_url = reverse('ticket:ticket-linked-issues', kwargs={'ticketIdOrUrl': self.ticket.id})

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

    def test_ticket_type_and_priority_list_apis_include_keys_values_and_icons(self):
        type_response = self.client.get(reverse('core:ticketTypeListApiVersion1'))
        priority_response = self.client.get(reverse('core:ticketPriorityListApiVersion1'))
        issue_response = self.client.get(self.api_url)

        self.assertEqual(type_response.status_code, 200)
        self.assertEqual(priority_response.status_code, 200)
        self.assertEqual(issue_response.status_code, 200)
        bug = next(option for option in type_response.data if option['key'] == Ticket.Type.BUG)
        high = next(option for option in priority_response.data if option['key'] == Ticket.Priority.HIGH)
        self.assertEqual(bug['value'], Ticket.Type.BUG.label)
        self.assertEqual(bug['icon'], Ticket.icons[Ticket.Type.BUG])
        self.assertEqual(high['value'], Ticket.Priority.HIGH.label)
        self.assertEqual(high['icon'], Ticket.icons[Ticket.Priority.HIGH])
        self.assertNotIn('editOptions', issue_response.data)

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

    def test_patch_assigns_and_clears_epic(self):
        epic = Ticket.objects.create(
            url='ONE-2',
            summary='Product epic',
            type=Ticket.Type.EPIC,
            project=self.project,
            reporter=self.user,
            columnStatus=self.status,
        )

        response = self.client.patch(
            self.api_url,
            {'epic': epic.id},
            format='json',
            QUERY_STRING=f'url={self.ticket.url}',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['epic']['id'], epic.id)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.epic, epic)

        response = self.client.patch(
            self.api_url,
            {'epic': None},
            format='json',
            QUERY_STRING=f'url={self.ticket.url}',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data['epic'])
        self.ticket.refresh_from_db()
        self.assertIsNone(self.ticket.epic)

    def test_patch_rejects_non_epic_as_epic(self):
        other_ticket = Ticket.objects.create(
            url='ONE-2',
            summary='Regular issue',
            project=self.project,
            reporter=self.user,
            columnStatus=self.status,
        )

        response = self.client.patch(
            self.api_url,
            {'epic': other_ticket.id},
            format='json',
            QUERY_STRING=f'url={self.ticket.url}',
        )

        self.assertEqual(response.status_code, 400)
        self.ticket.refresh_from_db()
        self.assertIsNone(self.ticket.epic)

    def test_patch_assigns_and_clears_parent(self):
        parent = Ticket.objects.create(
            url='ONE-2',
            summary='Parent ticket',
            type=Ticket.Type.SUB_TASK,
            project=self.project,
            reporter=self.user,
            columnStatus=self.status,
        )

        response = self.client.patch(
            self.api_url,
            {'parent': parent.id},
            format='json',
            QUERY_STRING=f'url={self.ticket.url}',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['parent']['id'], parent.id)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.parent, parent)

        response = self.client.patch(
            self.api_url,
            {'parent': None},
            format='json',
            QUERY_STRING=f'url={self.ticket.url}',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data['parent'])
        self.ticket.refresh_from_db()
        self.assertIsNone(self.ticket.parent)

    def test_patch_rejects_epic_as_parent(self):
        epic = Ticket.objects.create(
            url='ONE-2',
            summary='Project epic',
            type=Ticket.Type.EPIC,
            project=self.project,
            reporter=self.user,
            columnStatus=self.status,
        )

        response = self.client.patch(
            self.api_url,
            {'parent': epic.id},
            format='json',
            QUERY_STRING=f'url={self.ticket.url}',
        )

        self.assertEqual(response.status_code, 400)
        self.ticket.refresh_from_db()
        self.assertIsNone(self.ticket.parent)

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

    def test_epic_live_search_returns_only_epics(self):
        epic = Ticket.objects.create(
            url='ONE-2',
            summary='Project epic',
            type=Ticket.Type.EPIC,
            project=self.project,
            reporter=self.user,
            columnStatus=self.status,
        )
        Ticket.objects.create(
            url='ONE-3',
            summary='Regular issue',
            project=self.project,
            reporter=self.user,
            columnStatus=self.status,
        )

        response = self.client.get(self.ticket_search_url, {'epicOnly': 'true'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['id'] for item in response.data], [epic.id])

    def test_parent_live_search_returns_only_subtasks_and_excludes_requested_tickets(self):
        Ticket.objects.create(
            url='ONE-2',
            summary='Project epic',
            type=Ticket.Type.EPIC,
            project=self.project,
            reporter=self.user,
            columnStatus=self.status,
        )
        parent_ticket = Ticket.objects.create(
            url='ONE-3',
            summary='Parent subtask',
            type=Ticket.Type.SUB_TASK,
            project=self.project,
            reporter=self.user,
            columnStatus=self.status,
        )
        Ticket.objects.create(
            url='ONE-4',
            summary='Regular issue',
            project=self.project,
            reporter=self.user,
            columnStatus=self.status,
        )

        response = self.client.get(
            self.ticket_search_url,
            {'subTaskOnly': 'true', 'excludeTicketIds': [self.ticket.id]},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['id'] for item in response.data], [parent_ticket.id])

    def test_ticket_page_shows_epic_field_when_no_epic_is_assigned(self):
        response = self.client.get(self.ticket_page_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-inline-field="epic"')
        self.assertContains(response, 'Add epic')
        self.assertContains(response, 'data-inline-field="parent"')
        self.assertContains(response, 'Add parent')

    def test_index_dashboard_shows_my_work_and_hides_private_project_tickets(self):
        self.ticket.assignee = self.user
        self.ticket.save(update_fields=['assignee'])
        private_project = Project.objects.create(
            name='Private project',
            code='PRIVATE',
            description='',
            lead=User.objects.create_user(username='private-lead'),
            isPrivate=True,
        )
        private_status = self.create_status(private_project, 'Private To Do')
        private_ticket = Ticket.objects.create(
            url='PRIVATE-1',
            summary='Private assigned issue',
            project=private_project,
            reporter=self.user,
            assignee=self.user,
            columnStatus=private_status,
        )

        response = self.client.get(reverse('core:index-view'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['openTicketCount'], 1)
        self.assertContains(response, self.ticket.url)
        self.assertNotContains(response, private_ticket.url)

    def test_index_dashboard_requires_login(self):
        self.client.logout()

        response = self.client.get(reverse('core:index-view'))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/login?next=/')

    def test_boards_page_only_renders_add_form_when_requested(self):
        boards_url = reverse('core:boards-view')

        response = self.client.get(boards_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'class="p-4 add-board-form"')

        response = self.client.get(boards_url, {'add': 'true'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="p-4 add-board-form"')

        response = self.client.get(boards_url, {'add': 'false'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'class="p-4 add-board-form"')

    def test_projects_page_only_renders_add_form_when_requested(self):
        projects_url = reverse('core:projects-view')

        response = self.client.get(projects_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'class="p-4 add-project-form"')

        response = self.client.get(projects_url, {'add': 'true'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="p-4 add-project-form"')

        response = self.client.get(projects_url, {'add': 'false'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'class="p-4 add-project-form"')

    def test_teams_page_only_renders_add_form_when_requested(self):
        teams_url = reverse('core:teams-view')

        response = self.client.get(teams_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'class="p-4 add-team-form"')

        response = self.client.get(teams_url, {'add': 'true'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="p-4 add-team-form"')

        response = self.client.get(teams_url, {'add': 'false'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'class="p-4 add-team-form"')

    def test_labels_page_only_renders_add_form_when_requested(self):
        labels_url = reverse('core:labels-view')

        response = self.client.get(labels_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'class="p-4 add-label-form"')

        response = self.client.get(labels_url, {'add': 'true'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="p-4 add-label-form"')

        response = self.client.get(labels_url, {'add': 'false'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'class="p-4 add-label-form"')

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
            {'ticketIds': [subtask.id]},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['id'] for item in response.data], [subtask.id])
        self.assertTrue(self.ticket.subTask.filter(id=subtask.id).exists())

    def test_ticket_subtasks_api_rejects_non_subtasks(self):
        response = self.client.post(
            self.subtasks_url,
            {'ticketIds': [self.ticket.id]},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(self.ticket.subTask.exists())

    def test_epic_issues_api_lists_creates_and_attaches_issues(self):
        epic = Ticket.objects.create(
            url='ONE-2',
            summary='Epic',
            type=Ticket.Type.EPIC,
            project=self.project,
            reporter=self.user,
            columnStatus=self.status,
        )
        epic_issues_url = reverse('ticket:ticket-epic-issues', kwargs={'ticketId': epic.id})
        existing_issue = Ticket.objects.create(
            url='ONE-3',
            summary='Existing issue',
            project=self.project,
            reporter=self.user,
            columnStatus=self.status,
        )

        response = self.client.get(epic_issues_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

        response = self.client.post(
            epic_issues_url,
            {'summary': 'New epic issue'},
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        created_issue = Ticket.objects.get(summary='New epic issue')
        self.assertEqual(created_issue.type, Ticket.Type.STORY)
        self.assertEqual(created_issue.epic, epic)
        self.assertEqual([issue['id'] for issue in response.data], [created_issue.id])

        response = self.client.post(
            epic_issues_url,
            {'ticketIds': [existing_issue.id]},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        existing_issue.refresh_from_db()
        self.assertEqual(existing_issue.epic, epic)
        self.assertEqual(
            {issue['id'] for issue in response.data},
            {created_issue.id, existing_issue.id},
        )

    def test_epic_issues_api_rejects_epic_tickets_and_non_epic_parent(self):
        epic = Ticket.objects.create(
            url='ONE-2',
            summary='Epic',
            type=Ticket.Type.EPIC,
            project=self.project,
            reporter=self.user,
            columnStatus=self.status,
        )
        epic_issues_url = reverse('ticket:ticket-epic-issues', kwargs={'ticketId': epic.id})

        response = self.client.post(
            epic_issues_url,
            {'ticketIds': [epic.id]},
            format='json',
        )
        self.assertEqual(response.status_code, 400)

        response = self.client.get(self.epic_issues_url)
        self.assertEqual(response.status_code, 404)

    def test_epic_ticket_page_shows_issue_create_and_attach_forms(self):
        epic = Ticket.objects.create(
            url='ONE-2',
            summary='Epic',
            type=Ticket.Type.EPIC,
            project=self.project,
            reporter=self.user,
            columnStatus=self.status,
        )

        response = self.client.get(reverse('ticket:ticket-view', kwargs={'url': epic.url}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'create-epic-issue-form')
        self.assertContains(response, 'add-epic-issues-form')
        self.assertContains(response, 'No issues found for this epic.')
        self.assertContains(response, 'id="epicIssueProgress"')
        self.assertNotIn('epicProgress', response.context)

    def test_ticket_linked_issues_api_lists_outgoing_and_incoming_links(self):
        outgoing_ticket = Ticket.objects.create(
            url='ONE-2',
            summary='Outgoing',
            project=self.project,
            reporter=self.user,
            columnStatus=self.status,
        )
        incoming_ticket = Ticket.objects.create(
            url='ONE-3',
            summary='Incoming',
            project=self.project,
            reporter=self.user,
            columnStatus=self.status,
        )
        TicketLink.objects.create(
            source=self.ticket,
            target=outgoing_ticket,
            linkType=TicketLink.LinkType.BLOCKS,
        )
        TicketLink.objects.create(
            source=incoming_ticket,
            target=self.ticket,
            linkType=TicketLink.LinkType.BLOCKS,
        )

        response = self.client.get(self.linked_issues_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['linkTypes'][0], {
            'value': TicketLink.LinkType.LINKED_TO_ACTION,
            'label': TicketLink.LinkType.LINKED_TO_ACTION.label,
        })
        groups_by_type = {group['linkType']: group['tickets'] for group in response.data['linkedIssues']}
        self.assertEqual(groups_by_type[TicketLink.LinkType.BLOCKS.label][0]['id'], outgoing_ticket.id)
        self.assertEqual(groups_by_type[TicketLink.LinkType.IS_BLOCKED_BY.label][0]['id'], incoming_ticket.id)

    def test_ticket_linked_issues_api_creates_links_without_page_refresh(self):
        target = Ticket.objects.create(
            url='ONE-2',
            summary='Linked target',
            project=self.project,
            reporter=self.user,
            columnStatus=self.status,
        )

        response = self.client.post(
            self.linked_issues_url,
            {
                'linkType': TicketLink.LinkType.BLOCKS,
                'ticketIds': [target.id],
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(TicketLink.objects.filter(
            source=self.ticket,
            target=target,
            linkType=TicketLink.LinkType.BLOCKS,
        ).exists())
        group = next(group for group in response.data['linkedIssues'] if group['linkType'] == 'blocks')
        self.assertEqual(group['tickets'][0]['id'], target.id)

    def test_ticket_linked_issues_api_rejects_self_links_and_invalid_link_types(self):
        self_link_response = self.client.post(
            self.linked_issues_url,
            {
                'linkType': TicketLink.LinkType.BLOCKS,
                'ticketIds': [self.ticket.id],
            },
            format='json',
        )
        invalid_type_response = self.client.post(
            self.linked_issues_url,
            {
                'linkType': 'NOT_A_LINK_TYPE',
                'ticketIds': [self.ticket.id + 1],
            },
            format='json',
        )

        self.assertEqual(self_link_response.status_code, 400)
        self.assertEqual(invalid_type_response.status_code, 400)
        self.assertFalse(TicketLink.objects.exists())

    def test_ticket_linked_issues_api_rejects_duplicate_targets(self):
        target = Ticket.objects.create(
            url='ONE-2',
            summary='Linked target',
            project=self.project,
            reporter=self.user,
            columnStatus=self.status,
        )

        response = self.client.post(
            self.linked_issues_url,
            {
                'linkType': TicketLink.LinkType.BLOCKS,
                'ticketIds': [target.id, target.id],
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(TicketLink.objects.exists())

    def test_ticket_page_renders_subtasks_from_the_api(self):
        response = self.client.get(self.ticket_page_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="subtaskList"')
        self.assertNotContains(response, 'ticket.subTask.all')
        self.assertNotContains(response, 'ticketLinks')

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
            'ticket:ticket-comment-detail',
            kwargs={'ticketId': self.ticket.id, 'pk': comment.id},
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
            'ticket:ticket-comment-detail',
            kwargs={'ticketId': self.ticket.id, 'pk': comment.id},
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
            'ticket:ticket-comment-detail',
            kwargs={'ticketId': self.ticket.id, 'pk': other_comment.id},
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
                'ticket:ticket-comment-detail',
                kwargs={'ticketId': self.ticket.id, 'pk': comment.id},
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
                'ticket:ticket-comment-detail',
                kwargs={'ticketId': self.ticket.id, 'pk': comment.id},
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
                'ticket:ticket-comment-detail',
                kwargs={'ticketId': self.ticket.id, 'pk': comment.id},
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
            'ticket:ticket-comment-detail',
            kwargs={'ticketId': self.ticket.id, 'pk': comment.id},
        )

        response = self.client.post(detail_url, {'reaction': 'applaud'}, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertFalse(comment.likes.exists())
        self.assertFalse(comment.dislikes.exists())
