import random
import string

from django.apps import apps
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import connection
from faker import Faker

from accounts.models import Profile, Team
from jira.models import Board, Column, ColumnStatus, Ticket, Project
from taskmaster import settings
from taskmaster.operations import seedDataOperations

all_tables = connection.introspection.table_names()

# CONSTANT VALUES
EMAIL_DOMAINS = ["@yahoo", "@gmail", "@outlook", "@hotmail"]
DOMAINS = [".co.uk", ".com", ".co.in", ".net", ".us"]
BOOLEAN = [True, False]
JOB_TITLE = ['Software Engineer', 'Project Owner', 'Project Manager', 'UX/UI Designer', 'Solutions Architect']
PROJECT_APPS = ['accounts', 'jira']
DEPARTMENT = ['Marketing & Proposals Department', 'Sales Department', 'Project Department', 'Designing Department',
              'Production Department', 'Maintenance Department', 'Store Department', 'Procurement Department',
              'Quality Department', 'Inspection department', 'Packaging Department', 'Finance Department',
              'Dispatch Department', 'Account Department', 'Research & Development Department',
              'Information Technology Department', 'Human Resource Department', 'Security Department',
              'Administration department']


def generateString():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))


def cleanInstall(request, excludeThisUser=True, removeExistingObjects=True):
    if excludeThisUser:
        User.objects.all().exclude(id=request.user.id).exclude(is_superuser=True).delete()

    if removeExistingObjects:
        for app in PROJECT_APPS:
            for model in apps.get_app_config(app).get_models():
                model.objects.all().delete()

    seedDataOperations.runSeedDataInstaller()

    users = createUserObjects()
    profiles = createProfileObjects(users)
    teams = createTeamObjects(users)
    return


def createUserObjects(limit=20, maxLimit=20):
    currentCount = User.objects.count()
    remaining = maxLimit - currentCount

    if limit == 0 or currentCount > maxLimit:
        return User.objects.all()[:limit]

    BULK_USERS = []
    uniqueEmails = []

    for _ in range(remaining):
        fake = Faker()
        firstName = fake.unique.first_name()
        lastName = fake.unique.last_name()
        email = firstName.lower() + '.' + lastName.lower() + random.choice(EMAIL_DOMAINS) + random.choice(DOMAINS)

        BULK_USERS.append(
            User(username=email, email=email, password=settings.TEST_PASSWORD, first_name=firstName, last_name=lastName)
        )
        uniqueEmails.append(email)

    User.objects.bulk_create(BULK_USERS)
    return User.objects.filter(email__in=uniqueEmails)


def createProfileObjects(users=None):
    if users is None or len(users) == 0:
        createUserObjects()
        users = User.objects.all().prefetch_related('profile')

    BULK_PROFILES = []

    for user in users:
        try:
            user.profile
        except Profile.DoesNotExist:
            BULK_PROFILES.append(
                Profile(
                    user=user,
                    publicName=user.get_full_name(),
                    jobTitle=random.choice(JOB_TITLE),
                    department=random.choice(DEPARTMENT)
                )
            )

    return Profile.objects.bulk_create(BULK_PROFILES)


def createTeamObjects(users=None):
    if users is None or len(users) == 0:
        users = createUserObjects()

    chunkSize = 5
    usersChunks = [users[i:i + chunkSize] for i in range(0, len(users), chunkSize)]
    teams = []

    for userGroup in usersChunks:
        team = Team()
        team.internalKey = generateString()
        team.isPrivate = random.choice(BOOLEAN)
        team.description = generateString()
        team.save()

        team.admins.add(userGroup[0])
        team.members.add(*userGroup[1:])

        teams.append(team)
    return teams


def createBoard(boardType=Board.Types.SCRUM, internalKey="Test board"):
    board = Board.objects.create(
        internalKey=internalKey,
        type=boardType,
    )
    # board.refresh_from_db()
    return board


def createColumns(board=None):
    board = board or createBoard()
    c1 = Column(board=board, internalKey='BACKLOG', category=Column.Category.TODO, orderNo=1)
    c2 = Column(board=board, internalKey='TO DO', category=Column.Category.TODO, orderNo=2)
    c3 = Column(board=board, internalKey='IN PROGRESS', category=Column.Category.IN_PROGRESS, orderNo=3)
    c4 = Column(board=board, internalKey='DONE', category=Column.Category.DONE, orderNo=4)

    Column.objects.bulk_create(
        [c1, c2, c3, c4]
    )
    return Column.objects.filter(board=board)


def createColumnStatus(board=None, columns=None):
    if board is None:
        board = createBoard()

    if columns is None or columns == []:
        columns = createColumns(board)

    columnStatusIndex = [
        ("OPEN", False, Column.Category.TODO),
        ("TO DO", False, Column.Category.TODO),
        ("IN PROGRESS", False, Column.Category.IN_PROGRESS),
        ("DONE", True, Column.Category.DONE),
    ]

    columnStatusList = [
        ColumnStatus(
            internalKey=columnStatusIndex[0],
            board=board,
            column=column,
            setResolution=columnStatusIndex[1],
            category=columnStatusIndex[2]
        )
        for columnStatusIndex, column in zip(columnStatusIndex, columns)
    ]

    ColumnStatus.objects.bulk_create(
        columnStatusList
    )

    return ColumnStatus.objects.filter(board=board)


def createUser():
    return createUserObjects(1, 2).first()


def createProject(lead=None):
    newProject = Project()
    newProject.internalKey = "Test project"
    newProject.code = "TESTPROJECT"
    newProject.description = "Test Description"
    newProject.lead = lead or createUser()
    newProject.status = None
    newProject.save()
    return newProject


def createTicket(columnStatus=None, project=None, issueType=None):
    if project is None:
        project = createProject()

    if issueType is None:
        issueType = next((i.id for i in cache.get('TICKET_ISSUE_TYPE') if i.code == 'BUG'))

    ticket = Ticket()
    ticket.internalKey = project.code + "-" + "1"
    ticket.summary = "Test summary"
    ticket.description = "Test description"
    ticket.resolution_id = next((i.id for i in cache.get('TICKET_RESOLUTIONS') if i.code == 'UNRESOLVED'))
    ticket.project = project
    ticket.assignee_id = project.lead.id
    ticket.reporter_id = project.lead.id
    ticket.issueType_id = issueType
    ticket.priority_id = next((i.id for i in cache.get('TICKET_PRIORITY') if i.code == 'MEDIUM'))
    ticket.columnStatus = columnStatus
    ticket.orderNo = 1
    ticket.save()
    return ticket
