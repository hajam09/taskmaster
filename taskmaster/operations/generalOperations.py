from django.contrib.auth.models import User


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
