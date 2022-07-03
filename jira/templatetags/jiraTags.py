from django import template

from accounts.models import Component, Profile
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
    return Component.objects.filter(componentGroup__code="TICKET_ISSUE_TYPE")


@register.simple_tag
def ticketPriorities():
    return Component.objects.filter(componentGroup__code="TICKET_PRIORITY")
