import random
import string

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.management.base import BaseCommand
from faker import Faker

from accounts.models import Profile, Component, Team
from jira.models import Project, ProjectComponent, Board, Label, Column, ColumnStatus, Ticket
from taskmaster.operations import bakerOperations

EMAIL_DOMAINS = ["@yahoo", "@gmail", "@outlook", "@hotmail"]
DOMAINS = [".co.uk", ".com", ".co.in", ".net", ".us"]
BOOLEAN = [True, False]


class Command(BaseCommand):
    help = 'Seed data installer'

    NUMBER_OF_PROFILES = 40
    NUMBER_OF_TEAMS = 50
    NUMBER_OF_PROJECTS = 100
    NUMBER_OF_PROJECT_COMPONENT = 30
    NUMBER_OF_BOARDS = 100
    NUMBER_OF_LABELS = 200
    NUMBER_OF_TICKETS = 10

    def handle(self, *args, **kwargs):

        # self.handler_deleteTickets()
        # self.handler_deleteColumnsAndColumnStatus()
        # self.handler_deleteBoards()
        # self.handler_deleteProjectComponents()
        # self.handler_deleteProject()
        # self.handler_deleteLabels()
        # self.handler_deleteTeams()
        # self.handler_deleteUsersAndProfiles()

        # self.handler_createUsersAndProfiles()
        # self.handler_createTeams()
        # self.handler_createLabels()
        # self.handler_createProject()
        # self.handler_createProjectComponents()
        # self.handler_createBoards()
        # self.handler_createColumnsAndColumnStatus()
        # self.handler_createTickets()

        self.stdout.write("Seed data installed successfully")

    def handler_deleteTeams(self):
        Team.objects.all().delete()

    def handler_createTeams(self):
        listOfTeams = []

        for i in range(Command.NUMBER_OF_TEAMS):
            faker = Faker()
            listOfTeams.append(
                Team(
                    internalKey=f"Team - {faker.pystr_format()}",
                    description=faker.name(),
                    isPrivate=random.choice([True, False])
                )
            )

        Team.objects.bulk_create(listOfTeams)
        allUsers = list(User.objects.all().values_list('id', flat=True))

        for team in Team.objects.all():
            team.admins.add(*random.sample(allUsers, 1))
            team.members.add(*random.sample(allUsers, random.randint(1, 5)))

    def handler_deleteUsersAndProfiles(self):
        Profile.objects.filter(user__is_superuser=True).delete()
        User.objects.exclude(is_superuser=True).delete()

    def handler_createUsersAndProfiles(self):
        BULK_USERS = []
        listOfProfiles = []
        uniqueEmails = []
        occupations = Component.objects.filter(componentGroup__code="JOB_TITLES")

        for i in range(Command.NUMBER_OF_PROFILES):
            faker = Faker()
            firstName = faker.unique.first_name()
            lastName = faker.unique.last_name()
            email = firstName.lower() + '.' + lastName.lower() + random.choice(EMAIL_DOMAINS) + random.choice(DOMAINS)
            user = User(username=email, email=email, first_name=firstName, last_name=lastName)
            user.set_password(firstName.lower() + '.' + lastName.lower())
            BULK_USERS.append(user)
            uniqueEmails.append(email)

        User.objects.bulk_create(BULK_USERS)

        for user in User.objects.all():
            listOfProfiles.append(
                Profile(
                    user=user,
                    publicName=None,
                    jobTitle=random.choice(occupations).internalKey,
                    department=None,
                )
            )

        Profile.objects.bulk_create(listOfProfiles)

    def handler_deleteProject(self):
        Project.objects.all().delete()

    def handler_createProject(self):
        listOfProjects = []
        allUsers = User.objects.all()
        for i in range(Command.NUMBER_OF_PROJECTS):
            faker = Faker()

            listOfProjects.append(
                Project(
                    internalKey=f"Project {faker.pystr_format()}",
                    code=''.join(random.choice(string.ascii_uppercase) for i in range(8)),
                    description=faker.name(),
                    lead=random.choice(allUsers),
                    status=random.choice(cache.get('PROJECT_STATUS'))
                    # databaseOperations.getObjectByCode(cache.get('PROJECT_STATUS'), "ON_GOING")
                )
            )

        Project.objects.bulk_create(listOfProjects)

    def handler_deleteProjectComponents(self):
        ProjectComponent.objects.all().delete()

    def handler_createProjectComponents(self):

        allUsers = User.objects.all()
        for project in Project.objects.all():
            listOfProjectsComponents = []
            for i in range(Command.NUMBER_OF_PROJECT_COMPONENT):
                faker = Faker()

                listOfProjectsComponents.append(
                    ProjectComponent(
                        internalKey=faker.pystr_format(),
                        project=project,
                        status=random.choice([ProjectComponent.Status.DRAFT, ProjectComponent.Status.ACTIVE,
                                              ProjectComponent.Status.IN_ACTIVE, ProjectComponent.Status.ARCHIVED]),
                        lead=random.choice(allUsers),
                        description=faker.pystr_format()
                    )
                )

            ProjectComponent.objects.bulk_create(listOfProjectsComponents)

    def handler_deleteBoards(self):
        Board.objects.all().delete()

    def handler_createBoards(self):
        listOfBoards = []
        allProjects = Project.objects.all()
        allUsers = User.objects.all()

        for i in range(Command.NUMBER_OF_BOARDS):
            faker = Faker()

            listOfBoards.append(
                Board(
                    internalKey=f"Board - {faker.pystr_format()}",
                    type=random.choice([Board.Types.SCRUM, Board.Types.KANBAN])
                )
            )

        Board.objects.bulk_create(listOfBoards)

        for board in Board.objects.all():
            numberOfProjectsToAdd = random.choice([1, 2, 3])
            sampleOfProjectsToAdd = random.sample(list(allProjects), numberOfProjectsToAdd)
            board.projects.add(*sampleOfProjectsToAdd)

            numberOfAdminsToAdd = random.choice([1, 2])
            numberOfMembersToAdd = random.choice([1, 2, 3, 4])

            sampleOfAdmins = random.sample(list(allUsers), numberOfAdminsToAdd)
            sampleOfMembers = random.sample(list(allUsers), numberOfMembersToAdd)

            board.admins.add(*sampleOfAdmins)
            board.members.add(*sampleOfMembers)

    def handler_deleteColumnsAndColumnStatus(self):
        ColumnStatus.objects.all().delete()
        Column.objects.all().delete()

    def handler_createColumnsAndColumnStatus(self):
        self.stdout.write("Running handler_createColumnsAndColumnStatus")

        def getCategory(obj, value):
            if value == "TODO":
                return obj.TODO
            if value == "IN_PROGRESS":
                return obj.IN_PROGRESS
            if value == "DONE":
                return obj.DONE
            raise NotImplemented

        for board in Board.objects.all():
            columnCount = board.boardColumns.count()
            c1 = Column(
                board_id=board.id,
                internalKey="Todo",
                category=getCategory(Column.Category, "TODO"),
                orderNo=columnCount + 1
            )
            c2 = Column(
                board_id=board.id,
                internalKey="In Progress",
                category=getCategory(Column.Category, "IN_PROGRESS"),
                orderNo=columnCount + 2
            )
            c3 = Column(
                board_id=board.id,
                internalKey="Done",
                category=getCategory(Column.Category, "DONE"),
                orderNo=columnCount + 3
            )
            Column.objects.bulk_create([c1, c2, c3])

        for board in Board.objects.all().prefetch_related('boardColumns'):
            boardColumns = board.boardColumns.all()
            ColumnStatus.objects.bulk_create(
                [
                    ColumnStatus(
                        internalKey="Todo",
                        board_id=board.id,
                        column=boardColumns[0],
                        category=getCategory(ColumnStatus.Category, "TODO")
                    ),
                    ColumnStatus(
                        internalKey="In Progress",
                        board_id=board.id,
                        column=boardColumns[1],
                        category=getCategory(ColumnStatus.Category, "IN_PROGRESS")
                    ),
                    ColumnStatus(
                        internalKey="Done",
                        board_id=board.id,
                        column=boardColumns[2],
                        setResolution=True,
                        category=getCategory(ColumnStatus.Category, "DONE")
                    ),
                ]
            )

    def handler_deleteLabels(self):
        Label.objects.all().delete()

    def handler_createLabels(self):
        listOfLabels = []
        for i in range(Command.NUMBER_OF_LABELS):
            faker = Faker()

            listOfLabels.append(
                Label(
                    internalKey=f"Label {faker.pystr_format()}",
                    code=''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10)),
                    colour=faker.color
                )
            )

        Label.objects.bulk_create(listOfLabels)

    def handler_deleteColumns(self):
        Column.objects.all().delete()
        ColumnStatus.objects.all().delete()

    def handler_createColumns(self):
        for board in Board.objects.all():
            columns = bakerOperations.createColumns(board)
            bakerOperations.createColumnStatus(board, columns)

    def handler_deleteTickets(self):
        Ticket.objects.all().delete()

    def handler_createTickets(self):
        counter = 1

        for board in Board.objects.filter(type=Board.Types.KANBAN):
            listOfTickets = []
            for columnStatus in ColumnStatus.objects.filter(board=board):
                for i in range(Command.NUMBER_OF_TICKETS):
                    ticket = bakerOperations.createTicket(
                        columnStatus,
                        random.choice(board.projects.all()),
                        random.choice(cache.get('TICKET_ISSUE_TYPE')).id,
                        False
                    )

                    faker = Faker()
                    ticket.summary = faker.pystr_format()
                    ticket.internalKey = ticket.internalKey[:-1] + str(counter)
                    counter += 1

                    listOfTickets.append(ticket)

            Ticket.objects.bulk_create(listOfTickets)

        components = list(ProjectComponent.objects.all().values_list('id', flat=True))

        for ticket in Ticket.objects.all():
            numberOfComponentsToAdd = random.randint(0, 5)
            ticket.component.add(*random.sample(components, numberOfComponentsToAdd))
