import random

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from faker import Faker

from core.models import Profile, Team, Project, Board, Label, Column, ColumnStatus, Ticket


class Command(BaseCommand):
    NUMBER_OF_USERS = 10
    NUMBER_OF_TEAMS = 3
    NUMBER_OF_PROJECTS = 20
    NUMBER_OF_BOARDS_PER_PROJECT = 2
    NUMBER_OF_LABELS = 20
    NUMBER_OF_COLUMN_STATUS_PER_COLUMN = 1
    NUMBER_OF_TICKETS_PER_COLUMN_STATUS = 2

    def handle(self, *args, **kwargs):
        faker = Faker()

        Ticket.objects.all().delete()
        Label.objects.all().delete()
        ColumnStatus.objects.all().delete()
        Column.objects.all().delete()
        Board.objects.all().delete()
        Project.objects.all().delete()
        Team.objects.all().delete()
        Profile.objects.all().delete()
        User.objects.all().exclude(is_superuser=True).delete()

        newUsers = []
        for _ in range(min(Command.NUMBER_OF_USERS, Command.NUMBER_OF_USERS - User.objects.count())):
            email = faker.unique.email()
            user = User(
                username=email,
                email=email,
                first_name=faker.unique.first_name(),
                last_name=faker.unique.last_name(),
            )
            user.set_password('admin')
            newUsers.append(user)
        createdUsers = User.objects.bulk_create(newUsers)

        Profile.objects.bulk_create([
            Profile(
                user=user,
                jobTitle=random.choice(Profile.JobTitle.values),
                department=faker.pystr_format()
            )
            for user in createdUsers
        ])

        allUsers = list(User.objects.all())
        for _ in range(min(Command.NUMBER_OF_USERS, Command.NUMBER_OF_USERS - Team.objects.count())):
            team = Team.objects.create(
                name=faker.pystr_format(),
                description=faker.paragraph(),
                isPrivate=faker.boolean(50)
            )
            team.admins.add(*random.sample(allUsers, min(2, len(allUsers))))
            team.members.add(*random.sample(allUsers, min(2, len(allUsers))))

        newProjects = []
        for _ in range(min(Command.NUMBER_OF_PROJECTS, Command.NUMBER_OF_PROJECTS - Project.objects.count())):
            project = Project.objects.create(
                name=faker.pystr_format(),
                code=''.join(faker.random_letters(4)).upper(),
                description=faker.paragraph(),
                startDate=faker.past_date(),
                endDate=faker.future_date(),
                status=random.choice(Project.Status.values),
                isPrivate=faker.boolean(50),
                lead=random.choice(allUsers),
            )
            project.members.add(*random.sample(allUsers, min(3, len(allUsers))))
            newProjects.append(project)

        for project in newProjects:
            for _ in range(min(Command.NUMBER_OF_BOARDS_PER_PROJECT, Command.NUMBER_OF_BOARDS_PER_PROJECT - Board.objects.filter(project=project).count())):
                board = Board.objects.create(
                    name=faker.pystr_format(),
                    type=random.choice(Board.Types.values),
                    project=project,
                )
                board.admins.add(*random.sample(allUsers, min(2, len(allUsers))))
                board.members.add(*random.sample(allUsers, min(2, len(allUsers))))

        labelList = [
            Label(
                name=faker.pystr_format(),
                code=faker.swift8(),
                colour=faker.hex_color()
            )
            for _ in range(min(Command.NUMBER_OF_LABELS, Command.NUMBER_OF_LABELS - Label.objects.count()))
        ]
        Label.objects.bulk_create(labelList)

        columnList = []
        for board in Board.objects.all():
            unMappedColumns = min(1, 1 - Column.objects.filter(board=board, status=Column.Status.UNMAPPED).count())
            backLogColumns = min(1, 1 - Column.objects.filter(board=board, status=Column.Status.BACK_LOG).count())
            todoColumns = min(1, 1 - Column.objects.filter(board=board, status=Column.Status.TODO).count())
            inProgressColumns = min(2, 2 - Column.objects.filter(board=board, status=Column.Status.IN_PROGRESS).count())
            doneColumns = min(1, 1 - Column.objects.filter(board=board, status=Column.Status.DONE).count())

            columnList.extend([
                Column(name='Unmapped', board=board, status=Column.Status.UNMAPPED)
                for _ in range(unMappedColumns)
            ])
            columnList.extend([
                Column(name='Back Log', board=board, status=Column.Status.BACK_LOG)
                for _ in range(backLogColumns)
            ])
            columnList.extend([
                Column(name=faker.pystr_format(), board=board, status=Column.Status.TODO)
                for _ in range(todoColumns)
            ])
            columnList.extend([
                Column(name=faker.pystr_format(), board=board, status=Column.Status.IN_PROGRESS)
                for _ in range(inProgressColumns)
            ])
            columnList.extend([
                Column(name='Done', board=board, status=Column.Status.DONE)
                for _ in range(doneColumns)
            ])
        Column.objects.bulk_create(columnList)

        columnStatusList = []
        for column in Column.objects.all():
            statusesToCreate = min(Command.NUMBER_OF_COLUMN_STATUS_PER_COLUMN, Command.NUMBER_OF_COLUMN_STATUS_PER_COLUMN - ColumnStatus.objects.filter(column=column).count())
            columnStatusList.extend([
                ColumnStatus(name=faker.pystr_format(), column=column)
                for _ in range(statusesToCreate)
            ])
        ColumnStatus.objects.bulk_create(columnStatusList)

        assigneeList = [i for i in allUsers]
        assigneeList.append(None)
        for columnStatus in ColumnStatus.objects.all():
            for _ in range(Command.NUMBER_OF_TICKETS_PER_COLUMN_STATUS):
                _project = columnStatus.column.board.project
                ticket = Ticket()
                ticket.url = f'{_project.code}-{Ticket.objects.filter(project=_project).count() + 1}'
                ticket.summary = faker.sentence()
                ticket.description = faker.paragraph(nb_sentences=5)
                ticket.storyPoints = faker.random_element([1, 2, 3, 5, 8, 13])

                ticket.type = faker.random_element(Ticket.Type.values)
                ticket.priority = faker.random_element(Ticket.Priority.values)

                ticket.project = _project
                ticket.assignee = random.choice(assigneeList)
                ticket.reporter = random.choice(allUsers)
                ticket.columnStatus = columnStatus
                ticket.modifiedDateTime = faker.date_between('-3w', '-1d')

                ticket.save()
