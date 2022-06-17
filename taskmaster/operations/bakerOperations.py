import random
import string

from django.apps import apps
from django.contrib.auth.models import User
from django.db import connection
from faker import Faker

from accounts.models import Profile, Team
from taskmaster.operations import seedDataOperations

all_tables = connection.introspection.table_names()

# CONSTANT VALUES
EMAIL_DOMAINS = ["@yahoo", "@gmail", "@outlook", "@hotmail"]
DOMAINS = [".co.uk", ".com", ".co.in", ".net", ".us"]
BOOLEAN = [True, False]
JOB_TITLE = ['Software Engineer', 'Project Owner', 'Project Manager', 'UX/UI Designer', 'Solutions Architect']
PROJECT_APPS = ['accounts', 'jira']


def generateString():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))


def cleanInstall(request, excludeThisUser=True, removeExistingObjects=True):
    if excludeThisUser:
        User.objects.all().exclude(id=request.user.id).exclude(is_superuser=True).delete()

    if removeExistingObjects:
        for app in PROJECT_APPS:
            for model in apps.get_app_config(app).get_models():
                model.object.all().delete()

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
        password = 'RanDomPasWord56'

        BULK_USERS.append(
            User(username=email, email=email, password=password, first_name=firstName, last_name=lastName)
        )
        uniqueEmails.append(email)

    User.objects.bulk_create(BULK_USERS)
    return User.objects.filter(email__in=uniqueEmails)


def createProfileObjects(users=None):
    if users is None or len(users) == 0:
        users = createUserObjects()

    requiredProfile = []

    for user in users:
        try:
            user.profile
        except Profile.DoesNotExist:
            requiredProfile.append(user)

    for user in User.objects.all():
        try:
            user.profile
        except Profile.DoesNotExist:
            if user not in requiredProfile:
                requiredProfile.append(user)

    # TODO: Convert this to list comprehension
    BULK_PROFILES = []

    for user in requiredProfile:
        BULK_PROFILES.append(
            Profile(
                user=user,
                publicName=user.get_full_name(),
                jobTitle=random.choice(JOB_TITLE),
            )
        )
    return Profile.object.bulk_create(BULK_PROFILES)


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
