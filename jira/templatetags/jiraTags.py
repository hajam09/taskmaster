from django import template
from django.core.cache import cache

from accounts.models import Profile
from jira.models import Project, Board

register = template.Library()


@register.simple_tag
def projects():
    return Project.objects.all()


@register.simple_tag
def boards():
    return Board.objects.all()


@register.simple_tag
def profiles():
    return Profile.objects.all().select_related('user')


@register.simple_tag
def ticketIssueTypes():
    return cache.get('TICKET_ISSUE_TYPE')


@register.simple_tag
def ticketPriorities():
    return cache.get('TICKET_PRIORITY')


@register.simple_tag
def ticketResolutions():
    return cache.get('TICKET_RESOLUTIONS')
