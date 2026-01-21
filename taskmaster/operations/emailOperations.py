from threading import Thread

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


def privateSendEmailToActivateAccount(currentSiteDomain, user: User):
    emailSubject = 'Activate your TaskMaster Account'
    fullName = user.get_full_name()
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    prtg = PasswordResetTokenGenerator()
    url = reverse('core:activate-account-view', kwargs={'encodedId': uid, 'token': prtg.make_token(user)})

    message = f'''
        Hi {fullName},
        \n
        Welcome to TaskMaster, thank you for your joining our service.
        We have created an account for you to unlock more features.
        \n
        please click this link below to verify your account
        http://{currentSiteDomain}{url}
        \n
        Thanks,
        The TaskMaster Team
    '''

    emailMessage = EmailMessage(emailSubject, message, settings.EMAIL_HOST_USER, [user.email])
    emailMessage.send()
    return


def sendEmailToActivateAccount(request, user: User):
    currentSiteDomain = get_current_site(request).domain
    Thread(target=privateSendEmailToActivateAccount, args=(currentSiteDomain, user)).start()


def privateSendEmailToSetPassword(currentSiteDomain, user: User):
    emailSubject = 'Request to change TaskMaster Password'
    fullName = user.get_full_name()
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    prtg = PasswordResetTokenGenerator()
    url = reverse('core:set-password-view', kwargs={'encodedId': uid, 'token': prtg.make_token(user)})

    message = f'''
            Hi {fullName},
            \n
            You have recently request to change your account password.
            Please click this link below to change your account password.
            \n
            http://{currentSiteDomain}{url}
            \n
            Thanks,
            The TaskMaster Team
        '''

    emailMessage = EmailMessage(emailSubject, message, settings.EMAIL_HOST_USER, [user.email])
    emailMessage.send()
    return


def sendEmailToSetPassword(request, user: User):
    currentSiteDomain = get_current_site(request).domain
    Thread(target=privateSendEmailToSetPassword, args=(currentSiteDomain, user)).start()

# def sendEmailToNotifyUserAddedToTeam(request, user: User):
#     fullName = user.get_full_name()
#     emailSubject = "OneQuiz: You have been added to a team!"
#     message = """
#         Hi {},
#         \n
#         You have been added to a new team.
#         If you think it was a mistake, then don't worry.
#         Simply go to the team page and you can remove yourself from the team. Its that easy.
#         \n
#         Team link: {}
#         \n
#         Thanks,
#         The OneQuiz Team
#     """.format(fullName, request.get_raw_uri())
#
#     emailMessage = EmailMessage(emailSubject, message, settings.EMAIL_HOST_USER, [user.email])
#     emailMessage.send()
#     return
