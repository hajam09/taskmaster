from django import template
from django.urls import reverse

from taskmaster.base.utils.navigationBar import linkItem, Icon

register = template.Library()


@register.simple_tag
def navigationPanel(request):
    links = [
        linkItem('Home', '', None),
    ]

    if request.user.is_authenticated:
        links.append(
            linkItem('Account', '', None, [
                linkItem('Dashboard', reverse('jira:dashboard-view'), Icon('', 'fas fa-chalkboard', '15')),
                linkItem('Teams', reverse('jira:teams-page'), Icon('', 'fa fa-users', '15')),
                linkItem('Projects', reverse('jira:projects-page'), Icon('', 'fas fa-project-diagram', '15')),
                linkItem('Boards', reverse('jira:boards-page'), Icon('&#xf24d;', 'far', '15')),
                linkItem('Settings', f"{reverse('accounts:account-settings')}?tab=profileAndVisibility", Icon('&#xf013;', 'fa', '15')),
                None,
                linkItem('Logout', reverse('accounts:logout'), Icon('', 'fas fa-sign-out-alt', '15')),
            ]),
        )
    else:
        links.append(
            linkItem('Login / Register', '', None, [
                linkItem('Register', reverse('accounts:register'), Icon('', 'fas fa-user-circle', '20')),
                None,
                linkItem('Login', reverse('accounts:login'), Icon('', 'fas fa-sign-in-alt', '20')),
            ]),
        )
    return links
