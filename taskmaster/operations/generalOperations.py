import os
import random
from django.conf import settings
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
    componentList = Component.objects.all().select_related('componentGroup')
    cache.set('TICKET_ISSUE_TYPE', [i for i in componentList if i.componentGroup.code == 'TICKET_ISSUE_TYPE'], None)
    cache.set('PROJECT_STATUS', [i for i in componentList if i.componentGroup.code == 'PROJECT_STATUS'], None)
    cache.set('TICKET_PRIORITY', [i for i in componentList if i.componentGroup.code == 'TICKET_PRIORITY'], None)
    cache.set('TICKET_RESOLUTIONS', [i for i in componentList if i.componentGroup.code == 'TICKET_RESOLUTIONS'], None)
    cache.set('FILE_ICONS', [i for i in componentList if i.componentGroup.code == 'FILE_ICONS'], None)


def getRandomAvatar():
    return "avatars/" + random.choice(os.listdir(os.path.join(settings.MEDIA_ROOT, "avatars/")))


def deleteImage(imageField):
    if imageField is None:
        return

    existingImage = os.path.join(settings.MEDIA_ROOT, imageField.name)
    try:
        if os.path.exists(existingImage) and "/media/avatars/" not in imageField.url:
            os.remove(existingImage)
    except ValueError:
        pass
