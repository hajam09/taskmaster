import random

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db.models import F
from faker import Faker

from core.models import (
    Board,
    Column,
    ColumnStatus,
    Label,
    Profile,
    Project,
    Sprint,
    Team,
    Ticket
)


class Command(BaseCommand):
    NUMBER_OF_USERS = 14
    NUMBER_OF_TEAMS = 3
    NUMBER_OF_PROJECTS = 2
    NUMBER_OF_BOARDS_PER_PROJECT = 2
    NUMBER_OF_LABELS = 20
    NUMBER_OF_COLUMN_STATUS_PER_COLUMN = 2
    NUMBER_OF_TICKETS_PER_COLUMN_STATUS = 5

    def __init__(self):
        super().__init__()
        self.faker = Faker('en_GB')

    def handle(self, *args, **kwargs):
        self.seedUser()
        self.seedTeam()
        self.seedProject()
        self.seedLabel()
        self.seedBoard()
        self.seedColumn()
        self.seedColumnStatus()
        self.seedTicket()

    def seedUser(self):
        Profile.objects.filter(user__is_superuser=False).delete()
        User.objects.filter(is_superuser=False).delete()

        hashed_password = make_password('admin')
        users_to_create = []

        for _ in range(self.NUMBER_OF_USERS):
            first_name = self.faker.unique.first_name()
            last_name = self.faker.unique.last_name()
            email = f'{first_name.lower()}.{last_name.lower()}@{self.faker.free_email_domain()}'

            user = User(
                first_name=first_name,
                last_name=last_name,
                email=email,
                username=email,
                password=hashed_password
            )
            users_to_create.append(user)

        User.objects.bulk_create(users_to_create)

        new_users = User.objects.filter(is_superuser=False).order_by('id')
        Profile.objects.bulk_create([
            Profile(
                user=user,
                jobTitle=random.choice(Profile.JobTitle.values),
                department=self.faker.pystr_format()
            )
            for user in new_users
        ])

    def seedTeam(self):
        users = list(User.objects.all())
        random.shuffle(users)

        Team.admins.through.objects.all().delete()
        Team.members.through.objects.all().delete()
        Team.objects.all().delete()
        chunk_size = len(users) // self.NUMBER_OF_TEAMS
        remainder = len(users) % self.NUMBER_OF_TEAMS

        start = 0
        for i in range(self.NUMBER_OF_TEAMS):
            end = start + chunk_size + (1 if i < remainder else 0)
            team_users = users[start:end]
            start = end

            team = Team.objects.create(
                name=self.faker.unique.company(),
                description=self.faker.paragraph(),
                isPrivate=self.faker.boolean(20)
            )
            team.admins.add(*team_users)
            team.members.add(*team_users)

    def seedProject(self):
        users = list(User.objects.all())
        Project.members.through.objects.all().delete()
        Project.objects.all().delete()
        for _ in range(self.NUMBER_OF_PROJECTS):
            project = Project.objects.create(
                name=self.faker.pystr_format(),
                code=''.join(self.faker.random_letters(4)).upper(),
                description=self.faker.paragraph(),
                startDate=self.faker.past_date(),
                endDate=self.faker.future_date(),
                status=random.choice(Project.Status.values),
                isPrivate=self.faker.boolean(20),
                lead=random.choice(users),
            )
            project.members.add(*random.sample(users, min(3, len(users))))

    def seedLabel(self):
        Label.objects.all().delete()
        labelList = [
            Label(
                name=self.faker.pystr_format(),
                code=self.faker.swift8(),
                colour=self.faker.hex_color()
            )
            for _ in range(self.NUMBER_OF_LABELS)
        ]
        Label.objects.bulk_create(labelList)

    def seedBoard(self):
        projects = list(Project.objects.all())
        users = list(User.objects.all())

        Board.admins.through.objects.all().delete()
        Board.members.through.objects.all().delete()
        Board.objects.all().delete()

        for project in projects:
            for _ in range(Command.NUMBER_OF_BOARDS_PER_PROJECT):
                board = Board.objects.create(
                    name=self.faker.pystr_format(),
                    type=random.choice(Board.Types.values),
                    project=project,
                )
                board.admins.add(*random.sample(users, min(2, len(users))))
                board.members.add(*random.sample(users, min(2, len(users))))

    def seedColumn(self):
        Column.objects.all().delete()
        boards = list(Board.objects.all())

        for board in boards:
            unmapped = Column(name='Unmapped', board=board, status=Column.Status.UNMAPPED)
            backLog = Column(name='Back Log', board=board, status=Column.Status.BACK_LOG)
            todo = Column(name='To Do', board=board, status=Column.Status.TODO)
            inProgress = Column(name='In Progress', board=board, status=Column.Status.IN_PROGRESS)
            done = Column(name='Done', board=board, status=Column.Status.DONE)
            Column.objects.bulk_create([unmapped, backLog, todo, inProgress, done])
        Column.objects.update(orderNo=F('id'))

    def seedColumnStatus(self):
        ColumnStatus.objects.all().delete()
        columns = list(Column.objects.all())
        columnToCreate = [
            ColumnStatus(
                name=self.faker.pystr_format(),
                column=column
            )
            for column in columns
            for _ in range(self.NUMBER_OF_COLUMN_STATUS_PER_COLUMN)
        ]
        ColumnStatus.objects.bulk_create(columnToCreate)
        ColumnStatus.objects.update(orderNo=F('id'))

    def _createTicket(self, project, counter, assignees, users, columnStatus):
        counter[0] += 1

        TYPE_WEIGHTS = {
            Ticket.Type.BUG: 1,
            Ticket.Type.STORY: 1,
            Ticket.Type.SUB_TASK: 1,
            Ticket.Type.TASK: 1,
            Ticket.Type.TEST: 1,
            Ticket.Type.SPIKE: 1,
            Ticket.Type.EPIC: 0.08,  # EPIC is rare
        }

        ticket = Ticket(
            url=f'{project.code}-{counter[0]}',
            summary=self.faker.sentence(),
            description=self.faker.paragraph(nb_sentences=5),
            storyPoints=random.choice([1, 2, 3, 5, 8, 13]),
            resolution=random.choice(Ticket.Resolution.values),
            type=random.choices(Ticket.Type.values, weights=[TYPE_WEIGHTS[t] for t in Ticket.Type.values], k=1)[0],
            priority=random.choice(Ticket.Priority.values),
            project=project,
            assignee=random.choice(assignees),
            reporter=random.choice(users),
            columnStatus=columnStatus,
        )
        return ticket

    def _createTicketsForColumns(self, columns, project, counter, assignees, users):
        tickets = []
        for column in columns:
            columnStatuses = ColumnStatus.objects.filter(column=column)

            for columnStatus in columnStatuses:
                for _ in range(self.NUMBER_OF_TICKETS_PER_COLUMN_STATUS):
                    ticket = self._createTicket(
                        project,
                        counter,
                        assignees,
                        users,
                        columnStatus
                    )
                    tickets.append(ticket)
        return tickets

    def seedTicket(self):
        Ticket.subTask.through.objects.all().delete()
        Ticket.label.through.objects.all().delete()
        Ticket.watchers.through.objects.all().delete()
        Sprint.tickets.through.objects.all().delete()
        Ticket.objects.all().delete()
        Sprint.objects.all().delete()

        users = list(User.objects.all())
        assignees = users + [None]

        data = {
            'kanban-tickets': [],
            'scrum-backlogs': [],
            'active-tickets': [],
            'future-tickets': [],
        }

        for project in list(Project.objects.all()):
            counter = [Ticket.objects.filter(project=project).count()]
            kBoards = Board.objects.filter(project=project, type=Board.Types.KANBAN)
            sBoards = Board.objects.filter(project=project, type=Board.Types.SCRUM)

            for board in kBoards:
                columns = Column.objects.filter(board=board)
                tickets = self._createTicketsForColumns(
                    columns, project, counter, assignees, users
                )

                kt = data['kanban-tickets']
                kt.extend(tickets)

            for board in sBoards:
                # -------- Backlog (not currently in any sprint) --------
                columns = Column.objects.filter(
                    board=board,
                    status__in=[Column.Status.UNMAPPED, Column.Status.BACK_LOG]
                )
                tickets = self._createTicketsForColumns(
                    columns, project, counter, assignees, users
                )
                sb = data['scrum-backlogs']
                sb.extend(tickets)

                # -------- Active Sprint (in to-do, in-progress and done) --------
                activeSprint = Sprint(
                    board=board,
                    name=f'{board.name} Sprint 1',
                    isActive=True,
                    isComplete=False,
                )
                columns = Column.objects.filter(
                    board=board,
                    status__in=[Column.Status.TODO, Column.Status.IN_PROGRESS, Column.Status.DONE]
                )
                tickets = self._createTicketsForColumns(
                    columns, project, counter, assignees, users
                )
                at = data['active-tickets']
                at.append({
                    'sprint': activeSprint,
                    'tickets': tickets
                })

                # -------- Future Sprint(in to-do) --------
                futureSprints = [
                    Sprint(
                        board=board,
                        name=f'{board.name} Sprint {i}',
                        isActive=False,
                        isComplete=False,
                    )
                    for i in range(2, 4)
                ]
                columns = Column.objects.filter(
                    board=board,
                    status=Column.Status.TODO
                )

                for sprint in futureSprints:
                    tickets = self._createTicketsForColumns(
                        columns, project, counter, assignees, users
                    )
                    ft = data['future-tickets']
                    ft.append({
                        'sprint': sprint,
                        'tickets': tickets
                    })

        tickets = []
        sprints = []
        tickets.extend(data['kanban-tickets'])
        tickets.extend(data['scrum-backlogs'])

        for item in data['active-tickets']:
            sprint = item['sprint']
            sprintTickets = item['tickets']

            sprints.append(sprint)
            tickets.extend(sprintTickets)

        for item in data['future-tickets']:
            sprint = item['sprint']
            sprintTickets = item['tickets']

            sprints.append(sprint)
            tickets.extend(sprintTickets)

        Ticket.objects.bulk_create(tickets)
        Sprint.objects.bulk_create(sprints)

        Ticket.objects.update(orderNo=F('id'))

        labels = list(Label.objects.all())
        for ticket in Ticket.objects.all():
            random.shuffle(labels)
            ticket.label.add(*random.sample(labels, 4))

        for item in data['active-tickets']:
            sprint = item['sprint']
            sprintTickets = item['tickets']
            sprint.tickets.add(*sprintTickets)

        for item in data['future-tickets']:
            sprint = item['sprint']
            sprintTickets = item['tickets']
            sprint.tickets.add(*sprintTickets)

        epicTickets = list(Ticket.objects.filter(type=Ticket.Type.EPIC))
        otherTickets = list(Ticket.objects.exclude(type=Ticket.Type.EPIC))
        random.shuffle(otherTickets)
        X = len(epicTickets) + 1
        otherTicketsAsChunks = [[] for _ in range(X)]

        for index, ticket in enumerate(otherTickets):
            otherTicketsAsChunks[index % X].append(ticket)

        for epic, chunk in zip(epicTickets, otherTicketsAsChunks):
            Ticket.objects.filter(pk__in=[t.pk for t in chunk]).update(epic=epic)
