import random
import string

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.management.base import BaseCommand
from faker import Faker

from accounts.models import Profile, Component
from jira.models import Project, ProjectComponent, Board, Label, Column, ColumnStatus, Ticket
from taskmaster.operations import databaseOperations, bakerOperations

EMAIL_DOMAINS = ["@yahoo", "@gmail", "@outlook", "@hotmail"]
DOMAINS = [".co.uk", ".com", ".co.in", ".net", ".us"]
BOOLEAN = [True, False]


class Command(BaseCommand):
    help = 'Seed data installer'

    NUMBER_OF_PROFILES = 10
    NUMBER_OF_PROJECTS = 50
    NUMBER_OF_PROJECT_COMPONENT = 10
    NUMBER_OF_BOARDS = 5
    NUMBER_OF_LABELS = 40
    NUMBER_OF_TICKETS = 40

    def handle(self, *args, **kwargs):

        # self.handler_deleteProjectComponents()
        self.handler_deleteProject()
        # self.handler_deleteBoards()
        self.handler_deleteUsersAndProfiles()
        # self.handler_deleteLabels()
        # self.handler_deleteColumns()
        # self.handler_deleteTickets()
        #
        self.handler_createUsersAndProfiles()
        self.handler_createProject()
        # self.handler_createProjectComponents()
        # self.handler_createBoards()
        # self.handler_createLabels()
        # self.handler_createColumns()
        # self.handler_createTickets()

        self.stdout.write("Seed data installed successfully")

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

        for user in User.objects.exclude(is_superuser=True):
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
                    internalKey=faker.pystr_format(),
                    code=faker.unique.first_name().capitalize(),
                    description=faker.name(),
                    lead=random.choice(allUsers),
                    status=databaseOperations.getObjectByCode(cache.get('PROJECT_STATUS'), "ON_GOING")
                )
            )

        Project.objects.bulk_create(listOfProjects)

    def handler_deleteProjectComponents(self):
        ProjectComponent.objects.all().delete()

    def handler_createProjectComponents(self):
        listOfProjectsComponents = []
        allUsers = User.objects.all()
        for project in Project.objects.all():
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
                    internalKey=faker.pystr_format(),
                    type=random.choice([Board.Types.SCRUM, Board.Types.KANBAN])
                )
            )

        Board.objects.bulk_create(listOfBoards)

        for board in Board.objects.all():
            numberOfProjectsToAdd = random.choice([1, 2])
            sampleOfProjectsToAdd = random.sample(list(allProjects), numberOfProjectsToAdd)
            board.projects.add(*sampleOfProjectsToAdd)

            numberOfAdminsToAdd = random.choice([1, 2])
            numberOfMembersToAdd = random.choice([1, 2, 3, 4])

            sampleOfAdmins = random.sample(list(allUsers), numberOfAdminsToAdd)
            sampleOfMembers = random.sample(list(allUsers), numberOfMembersToAdd)

            board.admins.add(*sampleOfAdmins)
            board.members.add(*sampleOfMembers)

    def handler_deleteLabels(self):
        Label.objects.all().delete()

    def handler_createLabels(self):
        listOfLabels = []
        for i in range(Command.NUMBER_OF_LABELS):
            faker = Faker()

            listOfLabels.append(
                Label(
                    internalKey=faker.pystr_format(),
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
        listOfTickets = []
        counter = 1

        for board in Board.objects.filter(type=Board.Types.KANBAN):
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

        Ticket.objects.bulk_create(listOfTickets, batch_size=Command.NUMBER_OF_TICKETS)
