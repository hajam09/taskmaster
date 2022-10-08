from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


def sendEmailToActivateAccount(request, user: User):
    if settings.DEBUG or user.is_active:
        return

    currentSite = get_current_site(request)
    emailSubject = "Activate your TaskMaster Account"
    fullName = user.get_full_name()
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    prtg = PasswordResetTokenGenerator()
    url = reverse('accounts:activate-account', kwargs={'encodedId': uid, "token": prtg.make_token(user)})

    message = """
        Hi {},
        \n
        Welcome to TaskMaster, thank you for your joining our service.
        We have created an account for you to unlock more features.
        \n
        please click this link below to verify your account
        http://{}{}
        \n
        Thanks,
        The TaskMaster Team
    """.format(fullName, currentSite.domain, url)

    emailMessage = EmailMessage(emailSubject, message, settings.EMAIL_HOST_USER, [user.email])
    emailMessage.send()
    return


def sendEmailToResetPassword(request, user: User):
    currentSite = get_current_site(request)
    emailSubject = "Request to change OneTutor Password"
    fullName = user.get_full_name()
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    prtg = PasswordResetTokenGenerator()
    url = reverse('accounts:password-reset', kwargs={'encodedId': uid, "token": prtg.make_token(user)})

    message = """
            Hi {},
            \n
            You have recently request to change your account password.
            Please click this link below to change your account password.
            \n
            http://{}{}
            \n
            Thanks,
            The TaskMaster Team
        """.format(fullName, currentSite.domain, url)

    emailMessage = EmailMessage(emailSubject, message, settings.EMAIL_HOST_USER, [user.email])
    emailMessage.send()
    return


def sendEmailToNotifyUserAddedToTeam(request, user: User):
    fullName = user.get_full_name()
    emailSubject = "TaskMaster: You have been added to a team!"
    message = """
        Hi {},
        \n
        You have been added to a new team.
        If you think it was a mistake, then don't worry.
        Simply go to the team page and you can remove yourself from the team. Its that easy.
        \n
        Team link: {}
        \n
        Thanks,
        The TaskMaster Team
    """.format(fullName, request.get_raw_uri())

    emailMessage = EmailMessage(emailSubject, message, settings.EMAIL_HOST_USER, [user.email])
    emailMessage.send()
    return
