import random

from django.contrib.auth.models import User
from faker import Faker

from taskmaster.settings import TEST_PASSWORD

EMAIL_DOMAINS = ["@yahoo", "@gmail", "@outlook", "@hotmail"]
DOMAINS = [".co.uk", ".com", ".co.in", ".net", ".us"]


def createNewUser():
    faker = Faker()

    firstName = faker.unique.first_name()
    lastName = faker.unique.last_name()
    email = firstName.lower() + '.' + lastName.lower() + random.choice(EMAIL_DOMAINS) + random.choice(DOMAINS)

    user = User.objects.create_user(
        username=email,
        email=email,
        password=TEST_PASSWORD,
        first_name=firstName,
        last_name=lastName
    )
    user.save()
    return user
