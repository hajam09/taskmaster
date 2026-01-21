from urllib.parse import urlencode

from colorfield.widgets import ColorWidget
from django import template
from django.core.paginator import Page
from django.db.models.query import QuerySet
from django.forms.widgets import (
    CheckboxInput,
    CheckboxSelectMultiple,
    ClearableFileInput,
    EmailInput,
    HiddenInput,
    NumberInput,
    PasswordInput,
    RadioSelect,
    Select,
    TextInput,
    Textarea,
    SelectMultiple,
    DateInput,
)
from django.urls import reverse
from django.utils.safestring import mark_safe

from core.models import Column

register = template.Library()


class Icon:

    def __init__(self, name, clazz, size):
        self.name = name
        self.clazz = clazz
        self.size = size


def getIcon(icon):
    if icon is None:
        return None
    return '<i style="font-size:{}px" class="{}">{}</i>'.format(icon.size, icon.clazz, icon.name)


def linkItem(name, url, icon=None, subLinks=None):
    return {'name': name, 'url': url, 'icon': getIcon(icon), 'subLinks': subLinks}


@register.simple_tag
def navigationPanel(request):
    links = [
    ]

    if request.user.is_authenticated:
        links.extend(
            [
                linkItem('Projects', reverse('core:projects-view'), None),
                linkItem('Boards', reverse('core:boards-view'), None),
                linkItem('Tickets', reverse('core:tickets-view'), None),
                linkItem('Teams', reverse('core:teams-view'), None),
                linkItem('Labels', reverse('core:labels-view'), None),
                linkItem('Account', '', None, [
                    linkItem('Profile', reverse('core:profile-view'), Icon('', 'fas fa-book-open', '15')),
                    None,
                    linkItem('Logout', reverse('core:logout-view'), Icon('', 'fas fa-sign-out-alt', '15')),
                ]),
            ]
        )
    else:
        links.append(
            linkItem('Login / Register', '', None, [
                linkItem('Register', reverse('core:register-view'), Icon('', 'fas fa-user-circle', '20')),
                None,
                linkItem('Login', reverse('core:login-view'), Icon('', 'fas fa-sign-in-alt', '20')),
            ]),
        )
    return links


@register.simple_tag
def renderFormFields(field):
    body = ''
    extra = ''
    if isinstance(field.field.widget, SelectMultiple):
        label = f'<span class="form-label">{field.label}</span>'
        body = str(field)
        extra = '</br>'
    elif isinstance(field.field.widget, ColorWidget) or isinstance(field.field.widget, DateInput):
        label = f'<span class="form-label">{field.label}</span>'
        body += f'''
            <div class="row">
                <div class="col">
                    <input type={field.widget_type} name={field.name} value={field.initial} style="width: 100%;">
                </div>
            </div>'''
    elif (isinstance(field.field.widget, ClearableFileInput) or isinstance(field.field.widget, NumberInput)
          or isinstance(field.field.widget, Select) or isinstance(field.field.widget, TextInput)
          or isinstance(field.field.widget, Textarea) or isinstance(field.field.widget, EmailInput)
          or isinstance(field.field.widget, PasswordInput)):
        label = f'<span class="form-label">{field.label}</span>'
        body = str(field)
    elif isinstance(field.field.widget, CheckboxInput):
        label = f'<span class="form-label"></span>'
        for checkbox in field.subwidgets:
            body += f'''
                <div class="row">
                    <div class="col-auto">
                        <div class="multiple-choice">
                            <input type={checkbox.data.get('type')} name={checkbox.data.get('name')}
                            id={checkbox.data.get('attrs').get('id')} class={checkbox.data.get('attrs').get('class')}
                            style="height: 34px; width: 34px;" {"required" if checkbox.data.get('selected') else ""}
                            {"checked" if checkbox.data.get('attrs').get('checked') else ""}>
                        </div>
                    </div>
                    <div class="col">
                        <label class="form-label" style="padding-top: 5px">{field.label}</label>
                        <small><b>{field.help_text}</b></small>
                    </div>
                </div>'''
    elif isinstance(field.field.widget, CheckboxSelectMultiple) or isinstance(field.field.widget, RadioSelect):
        label = f'<h5 class="form-label" style="font-size: 16px">{field.label}</h5>'
        for widget in field.subwidgets:
            body += f'''
                <div class="row">
                    <div class="col-auto">
                        <input type={widget.data.get('type')}
                            name={widget.data.get('name')}
                            value={widget.data.get('value')}
                            style="{widget.data.get('attrs').get('style')}"
                            id={widget.data.get('attrs').get('id')}
                            {"required" if widget.data.get('attrs').get('required') else ""}
                            {"disabled" if widget.data.get('attrs').get('disabled') else ""}
                            {"checked" if widget.data.get('selected') else ""}>
                    </div>
                    <div class="col">
                    <input type="text" class="form-control form-control-sm col" disabled="" value="{widget.data.get('label')}">
                </div>
            </div>'''
    elif isinstance(field.field.widget, HiddenInput):
        label = ''
        body = str(field)
    else:
        raise Exception(f'Unsupported field type: {field.field.widget.__class__}')
    return mark_safe(label + body + extra)


@register.simple_tag
def getAvatarImage(name=None, avatar="https://cdn3.iconfinder.com/data/icons/avatars-round-flat/33/man5-512.png"):
    body = f'''
        <img src="{avatar}"
        width="20px"
        title="{name or 'Unassigned'}"
        class="img-rounded"
        loading="lazy"
        style="margin-left: 10px; margin-right: -15px"/>
    '''
    return mark_safe(body)


@register.simple_tag
def renderSingleOrGroupUserAvatars(users):
    manAvatar = "https://cdn3.iconfinder.com/data/icons/avatars-round-flat/33/man5-512.png"

    def privateGetAvatarImage(name='', avatar=manAvatar):
        return f'''
            <img alt="{name}"
                class="avatar filter-by-alt"
                src={avatar}
                data-filter-by="alt">
        '''

    body = ''
    remainingCount = 0
    if not isinstance(users, (list, tuple, set, QuerySet)):
        users = [users]
        remainingCount = max(0, len(users) - 5)
        users = users[:5]

    if len(users) == 1:
        for user in users:
            body += f'''
                <span class="row">
                    <span class="col">
                         <span class="d-flex align-items-center">
                             {privateGetAvatarImage(name=None if user is None else user.get_full_name())}
                             &nbsp;
                             <span>{'Unassigned' if user is None else user.get_full_name()}</span>
                        </span>
                    </span>
                </span>
            '''
    else:
        body += '<ul class="avatars">'
        for user in users:
            body += f'''
                <li>
                    <a href="#" data-toggle="tooltip"
                       data-original-title="{user.get_full_name()}"
                       title="{user.get_full_name()}">
                    {privateGetAvatarImage(name=user.get_full_name())}
                    </a>
                </li>
            '''

        if remainingCount != 0:
            body += f'''
                <li>
                    <a href="#" data-toggle="tooltip"
                       data-original-title="{remainingCount}"
                       title="{remainingCount}">
                       {privateGetAvatarImage(
                name=f"{remainingCount}",
                avatar=f"https://dummyimage.com/126x128/000/fff&text={remainingCount}"
            )}
                    </a>
                </li>
            '''
        body += '</ul>'

    return mark_safe(body)


@register.simple_tag
def ticketComponent(ticket):
    strikethrough = 'strikethrough' if ticket.columnStatus.column.status == Column.Status.DONE else ''
    epic = f'''
        <span class="badge badge-primary float-right"
            style="background-color: {ticket.epic.colour}; margin-left: 14px; margin-bottom: 5px;">
            {ticket.epic.summary}
        </span>
    ''' if ticket.epic else ''
    body = f'''
        <div class="card mb-1 ticket-object-component border" data-identifier="{ticket.id}">
            <div class="card-body mt-1" style="margin-left: -10px; margin-right: -15px;"> {ticket.summary} </div>
            <div class="card-body" style="position: relative;top: 15px;left: -10px;">
                <div class="row align-items-center">{epic}</div>
                <div class="row align-items-center">
                    <div class="col d-flex align-items-center">
                        <img src="{ticket.ticketTypeIcon}" width="20px" title="{ticket.get_type_display()}">
                        <a class="ml-2 {strikethrough}" href="{ticket.getUrl}">{ticket.url}</a>
                    </div>
                    <div class="col-auto ml-auto d-flex align-items-center">
                        <span class="badge badge-pill" style="background-color:#f0f0f0; font-size: 11px">{ticket.storyPoints}</span>
                        <img src="{ticket.ticketPriorityIcon}" width="20px" style="margin-left:10px" title="{ticket.get_priority_display()}">
                        {getAvatarImage()}
                    </div>
                </div>
            </div>
        </div>
    '''
    return mark_safe(body)


@register.simple_tag
def ticketHorizontalBarComponent(ticket, showEpicLabel=True):
    strikethrough = 'strikethrough' if ticket.columnStatus.column.status == Column.Status.DONE else ''
    epic = f'''
        <span class="badge badge-primary float-right" style="margin-top: 4.5px; background-color: {ticket.epic.colour}"
            data-toggle="tooltip" data-placement="top" title="{ticket.summary}">
            {ticket.epic.summary[:10].rstrip() + '...' if len(ticket.epic.summary) > 10 else ticket.epic}
        </span>
    ''' if ticket.epic and showEpicLabel else ''
    summary = ticket.summary[:70].rstrip() + '...' if len(ticket.summary) > 70 else ticket.summary

    body = f'''
        <li class="list-group-item ticket-object-component mt-1" id="ticket-{ticket.id}" identifier="{ticket.id}">
            <img src="{ticket.ticketTypeIcon}" width="20px" title="{ticket.get_type_display()}" class="img-rounded"
                loading="lazy">
            &nbsp;
            <img src="{ticket.ticketPriorityIcon}" width="20px" title="{ticket.get_priority_display()}"
                class="img-rounded" loading="lazy" style="margin-left: 10px"/>
            <a class="ml-2 {strikethrough}" href="{ticket.getUrl}">{ticket.url}</a>
            &nbsp;
            <span data-toggle="tooltip" data-placement="top" title="{ticket.summary}">{summary}</span>
            <span class="float-right ml-2" style="margin-right: 10px;">{getAvatarImage()}</span>
            <span class="badge badge-pill float-right ml-3" style="background-color: #f0f0f0; margin-top: 4.5px;">
                {ticket.storyPoints}
            </span>
            <span class="badge badge-primary float-right ml-3" style="margin-top: 4.5px;">{ticket.columnStatus.name}</span>
            {epic}
        </li>
    '''
    return mark_safe(body)


@register.simple_tag
def boardSettingsLinksComponent(board, visibility):
    boardSettingsViewUrl = reverse('core:board-settings-view', kwargs={'url': board.url})
    boardViewUrl = reverse('core:board-view', kwargs={'url': board.url})
    boardBacklogViewUrl = reverse('core:board-backlog-view', kwargs={'url': board.url})
    body = f'''
        <button class="btn btn-primary" id="toggle-button" style="left: 10px; top: 10px;">
            &#9776;
        </button>
        <p></p>
        <div class="card idCardWideComponent" id="nav-bar-element"
            style="padding: 0px; display: {'block' if visibility == 'show' else 'none'};">
            <ul class="list-group list-group-flush">
                <li class="list-group-item"><b class="card-title text-uppercase">Links</b></li>
                <li class="list-group-item">
                    <a href="{boardViewUrl}">Board</a>
                </li>
                <li class="list-group-item">
                    <a href="{boardBacklogViewUrl}">Backlog</a>
                </li>
                <li class="list-group-item"><b class="card-title text-uppercase">Settings</b></li>
                <li class="list-group-item">
                    <a href="{boardSettingsViewUrl + '?' + urlencode({'tab': 'general'})}">General</a>
                </li>
                <li class="list-group-item">
                    <a href="{boardSettingsViewUrl + '?' + urlencode({'tab': 'columns'})}">Columns</a>
                </li>
            </ul>
        </div>
    '''
    return mark_safe(body)


@register.simple_tag
def paginationComponent(request, objects: Page):
    if not objects.has_other_pages():
        return mark_safe('<span></span>')

    parameters = request.GET.copy()
    currentParameters = parameters.copy()
    parameters.pop('page', None)
    query = urlencode(parameters)

    def createUrlWithPage(number):
        return f"?page={number}&{query}" if query else f"?page={number}"

    def hasParametersChanged():
        return currentParameters.get('tab') != request.GET.get('tab') or currentParameters.get(
            'query') != request.GET.get('query')

    if hasParametersChanged():
        pageNumber = 1
    else:
        pageNumber = int(request.GET.get('page') or 1)

    if objects.has_previous():
        previousPageLink = f'''
        <li class="page-item">
            <a class="page-link" href="{createUrlWithPage(objects.previous_page_number())}" tabindex="-1">Previous</a>
        </li>
        '''
        firstPageLink = f'''
        <li class="page-item">
            <a class="page-link" href="{createUrlWithPage(1)}" tabindex="-1">First</a>
        </li>
        '''
    else:
        previousPageLink = f'''
        <li class="page-item disabled">
            <a class="page-link" href="#" tabindex="-1">Previous</a>
        </li>
        '''
        firstPageLink = f'''
        <li class="page-item disabled">
            <a class="page-link" href="#" tabindex="-1">First</a>
        </li>
        '''

    # Next and last page links
    if objects.has_next():
        nextPageLink = f'''
        <li class="page-item">
            <a class="page-link" href="{createUrlWithPage(objects.next_page_number())}" tabindex="-1">Next</a>
        </li>
        '''
        lastPageLink = f'''
        <li class="page-item">
            <a class="page-link" href="{createUrlWithPage(objects.paginator.num_pages)}" tabindex="-1">Last</a>
        </li>
        '''
    else:
        nextPageLink = f'''
        <li class="page-item disabled">
            <a class="page-link" href="#" tabindex="-1">Next</a>
        </li>
        '''
        lastPageLink = f'''
        <li class="page-item disabled">
            <a class="page-link" href="#" tabindex="-1">Last</a>
        </li>
        '''

    # Page number links
    pageNumberLinks = ''
    EITHER_SIDE_PAGE_LIMIT = 20
    pageRange = objects.paginator.page_range
    if pageRange.stop > EITHER_SIDE_PAGE_LIMIT:
        currentPage = pageNumber
        minRange = currentPage - EITHER_SIDE_PAGE_LIMIT // 2
        maxRange = currentPage + EITHER_SIDE_PAGE_LIMIT // 2

        if minRange <= 0:
            minRange = 1
        if maxRange > pageRange.stop:
            maxRange = pageRange.stop

        pageRange = range(minRange, maxRange)

    for pageNumber in pageRange:
        if objects.number == pageNumber:
            pageNumberLinks += f'''
                <li class="page-item active"><a class="page-link" href="#">{pageNumber}</a></li>
            '''
        else:
            pageNumberLinks += f'''
                <li class="page-item"><a class="page-link" href="{createUrlWithPage(pageNumber)}">{pageNumber}</a></li>
            '''

    itemContent = f'''
    <div class="row">
        <div class="col-md-12" style="width: 1100px;">
            <nav aria-label="Page navigation example">
                <ul class="pagination justify-content-center">
                    {firstPageLink}
                    {previousPageLink}
                    {pageNumberLinks}
                    {nextPageLink}
                    {lastPageLink}
                </ul>
            </nav>
        </div>
    </div>
    '''
    return mark_safe(itemContent)
