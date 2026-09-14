import re

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.exceptions import FieldDoesNotExist
from django.core.mail import EmailMessage
from django.db.models import Q
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from core.models import TicketLink

ticketPattern = re.compile(r'^([A-Z]+)-?(\d+)$')

ticketLinkInverts = {
    TicketLink.LinkType.LINKED_TO_ACTION: TicketLink.LinkType.LINKED_FROM_ACTION,
    TicketLink.LinkType.LINKED_FROM_ACTION: TicketLink.LinkType.LINKED_TO_ACTION,
    TicketLink.LinkType.BLOCKS: TicketLink.LinkType.IS_BLOCKED_BY,
    TicketLink.LinkType.IS_BLOCKED_BY: TicketLink.LinkType.BLOCKS,
    TicketLink.LinkType.IS_A_CHANGE_TO: TicketLink.LinkType.CHANGED_BY,
    TicketLink.LinkType.CHANGED_BY: TicketLink.LinkType.IS_A_CHANGE_TO,
    TicketLink.LinkType.CLONES: TicketLink.LinkType.IS_CLONED_BY,
    TicketLink.LinkType.IS_CLONED_BY: TicketLink.LinkType.CLONES,
    TicketLink.LinkType.IS_DEPENDENT_ON: TicketLink.LinkType.IS_DEPENDENCY_OF,
    TicketLink.LinkType.IS_DEPENDENCY_OF: TicketLink.LinkType.IS_DEPENDENT_ON,
    TicketLink.LinkType.DUPLICATED: TicketLink.LinkType.IS_DUPLICATED_BY,
    TicketLink.LinkType.IS_DUPLICATED_BY: TicketLink.LinkType.DUPLICATED,
    TicketLink.LinkType.IMPACTS: TicketLink.LinkType.IMPACTED_BY,
    TicketLink.LinkType.IMPACTED_BY: TicketLink.LinkType.IMPACTS,
    TicketLink.LinkType.REPLACES: TicketLink.LinkType.IS_REPLACED_BY,
    TicketLink.LinkType.IS_REPLACED_BY: TicketLink.LinkType.REPLACES,
    TicketLink.LinkType.LINKED_TO_RISK: TicketLink.LinkType.LINKED_FROM_RISK,
    TicketLink.LinkType.LINKED_FROM_RISK: TicketLink.LinkType.LINKED_TO_RISK,
    TicketLink.LinkType.CAUSES: TicketLink.LinkType.IS_CAUSED_BY,
    TicketLink.LinkType.IS_CAUSED_BY: TicketLink.LinkType.CAUSES,
    TicketLink.LinkType.CONTAINS: TicketLink.LinkType.IS_CONTAINED_BY,
    TicketLink.LinkType.IS_CONTAINED_BY: TicketLink.LinkType.CONTAINS,
    TicketLink.LinkType.CONTRIBUTES_TO: TicketLink.LinkType.IS_CONTRIBUTED_BY,
    TicketLink.LinkType.IS_CONTRIBUTED_BY: TicketLink.LinkType.CONTRIBUTES_TO,
    TicketLink.LinkType.FULLY_IMPLEMENTS: TicketLink.LinkType.IS_FULLY_IMPLEMENTED_BY,
    TicketLink.LinkType.IS_FULLY_IMPLEMENTED_BY: TicketLink.LinkType.FULLY_IMPLEMENTS,
    TicketLink.LinkType.RELATES: TicketLink.LinkType.IS_RELATED_BY,
    TicketLink.LinkType.IS_RELATED_BY: TicketLink.LinkType.RELATES,
    TicketLink.LinkType.PARTIALLY_IMPLEMENTS: TicketLink.LinkType.IS_PARTIALLY_IMPLEMENTED_BY,
    TicketLink.LinkType.IS_PARTIALLY_IMPLEMENTED_BY: TicketLink.LinkType.PARTIALLY_IMPLEMENTS,
    TicketLink.LinkType.STARTS_WITH: TicketLink.LinkType.FINISHES_WITH,
    TicketLink.LinkType.FINISHES_WITH: TicketLink.LinkType.STARTS_WITH,
    TicketLink.LinkType.HAS_TO_BE_DONE_BEFORE: TicketLink.LinkType.HAS_TO_BE_DONE_AFTER,
    TicketLink.LinkType.HAS_TO_BE_DONE_AFTER: TicketLink.LinkType.HAS_TO_BE_DONE_BEFORE,
    TicketLink.LinkType.HAS_TO_BE_STARTED_TOGETHER_WITH: TicketLink.LinkType.HAS_TO_BE_FINISHED_TOGETHER_WITH,
    TicketLink.LinkType.HAS_TO_BE_FINISHED_TOGETHER_WITH: TicketLink.LinkType.HAS_TO_BE_STARTED_TOGETHER_WITH,
    TicketLink.LinkType.IS_PARENT_TASK_OF: TicketLink.LinkType.IS_SUBTASK_OK,
    TicketLink.LinkType.IS_SUBTASK_OK: TicketLink.LinkType.IS_PARENT_TASK_OF,
}


def updateOrderNoForListOfObjects(model, ids):
    orderNoInOrder = sorted(m.orderNo for m in model)
    idAndModelMap = {m.id: m for m in model}

    for index, _id in enumerate(ids):
        idAndModelMap[int(_id)].orderNo = orderNoInOrder[index]
    return model


def groupLinkedIssues(ticket):
    links = TicketLink.objects.filter(Q(source=ticket) | Q(target=ticket)).select_related(
        'source__columnStatus__column', 'target__columnStatus__column', 'source__epic', 'target__epic'
    )
    result = {}

    for link in links:
        if link.source_id == ticket.id:
            linkType = link.get_linkType_display()
            linkedTicket = link.target
        else:
            linkType = ticketLinkInverts[link.linkType].label
            linkedTicket = link.source

        result.setdefault(linkType, []).append(linkedTicket)

    return result


def buildQuotedAwareSearchQuery(queryset, searchTerm, searchFields):
    """
    Builds a Django Q object for quote-aware multi-field search.

    Args:
        queryset: initial queryset (not modified)
        searchTerm: search string, can contain single/double quotes
        searchFields: list of field names to search in

    Returns:
        Filtered queryset
    """
    if not searchTerm:
        return queryset

    # Extract quoted phrases (single or double quotes)
    quotedPhrases = re.findall(r'"([^"]+)"|\'([^\']+)\'', searchTerm)
    quotedPhrases = [q[0] or q[1] for q in quotedPhrases]

    # Remove quoted phrases from searchTerm
    tempSearch = re.sub(r'"[^"]+"|\'[^\']+\'', '', searchTerm)
    words = tempSearch.split()

    # Prepare components
    quotedPhrasesComponents = [{'value': phrase, 'exact': True} for phrase in quotedPhrases]
    wordsComponents = [{'value': word, 'exact': False} for word in words]
    searchComponents = quotedPhrasesComponents + wordsComponents

    combinedQ = Q()
    for component in searchComponents:
        componentQ = Q()
        for field in searchFields:
            # Determine if the field is a direct field on the model
            rootField = field.split('__')[0]
            try:
                modelField = queryset.model._meta.get_field(rootField)
                isDirectField = not (modelField.is_relation and not modelField.many_to_many)
            except FieldDoesNotExist:
                isDirectField = False

            if component['exact'] and isDirectField:
                # Only direct fields support regex
                pattern = rf'\b{re.escape(component["value"])}\b'
                componentQ |= Q(**{f"{field}__iregex": pattern})
            else:
                # Related fields or unquoted words
                componentQ |= Q(**{f"{field}__icontains": component["value"]})
        combinedQ &= componentQ  # AND between components

    return queryset.filter(combinedQ).distinct()


def buildFilterMapQuery(request, FILTER_MAP):
    filters = {}

    for param, field in FILTER_MAP.items():
        value = request.GET.get(param)
        if value:
            filters[field] = [
                v.strip() for v in value.split(',') if v.strip()
            ]

    VISIBILITY_MAP = {
        'PRIVATE': True,
        'PUBLIC': False,
    }

    visibility = request.GET.get('visibility')
    if visibility and visibility.upper() in VISIBILITY_MAP:
        filters['isPrivate'] = VISIBILITY_MAP[visibility.upper()]

    return filters


def sendEmailToActivateAccount(currentSiteDomain, user: User):
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


def sendEmailToSetPassword(currentSiteDomain, user: User):
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


def sendEmailToNotifyUserAddedToTeam(request, user: User):
    emailSubject = 'TaskMaster: You have been added to a team!'
    fullName = user.get_full_name()

    message = f'''
        Hi {fullName},
        \n
        You have been added to a new team.
        If you think it was a mistake, then don't worry.
        Simply go to the team page and you can remove yourself from the team. Its that easy.
        \n
        Team link: {request.get_raw_uri()}
        \n
        Thanks,
        The TaskMaster Team
    '''

    emailMessage = EmailMessage(emailSubject, message, settings.EMAIL_HOST_USER, [user.email])
    emailMessage.send()
    return
