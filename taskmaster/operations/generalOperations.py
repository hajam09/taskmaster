from django.contrib.auth.models import User
from django.core.cache import cache

from accounts.models import Component


def isPasswordStrong(password):
    if len(password) < 8:
        return False

    if not any(letter.isalpha() for letter in password):
        return False

    if not any(capital.isupper() for capital in password):
        return False

    if not any(number.isdigit() for number in password):
        return False

    return True


def serializeUserVersion1(user: User):
    if user is None:
        return None

    return {
        "id": user.pk or None,
        "firstName": user.first_name,
        "lastName": user.last_name,
        "icon": user.profile.profilePicture.url,
    }


def serializeUserVersion2(user: User):
    if user is None:
        return None

    return {
        "id": user.pk or None,
        "fullName": user.get_full_name(),
        "icon": user.profile.profilePicture.url,
    }


def setCaches():
    cache.set('TICKET_ISSUE_TYPE', Component.objects.filter(componentGroup__code='TICKET_ISSUE_TYPE'), None)
    cache.set('PROJECT_STATUS', Component.objects.filter(componentGroup__code='PROJECT_STATUS'), None)
    cache.set('TICKET_PRIORITY', Component.objects.filter(componentGroup__code='TICKET_PRIORITY'), None)
    cache.set('TICKET_RESOLUTIONS', Component.objects.filter(componentGroup__code='TICKET_RESOLUTIONS'), None)
    cache.set('FILE_ICONS', Component.objects.filter(componentGroup__code='FILE_ICONS'), None)
