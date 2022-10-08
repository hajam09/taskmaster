import os
import random

from colorfield.fields import ColorField
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from accounts.models import BaseModel, generateString, Component


def getRandomProjectIcon():
    return "project-icons/" + random.choice(os.listdir(os.path.join(settings.MEDIA_ROOT, "project-icons/")))


class Project(BaseModel):
    internalKey = models.CharField(max_length=2048, unique=True)
    code = models.CharField(max_length=2048, unique=True, db_index=True)
    url = models.SlugField(max_length=10, editable=settings.DEBUG, unique=True, default=generateString, db_index=True)
    description = models.TextField()
    lead = models.ForeignKey(User, on_delete=models.CASCADE)
    startDate = models.DateField(default=timezone.now)
    endDate = models.DateField(default=timezone.datetime.max)
    status = models.ForeignKey(Component, null=True, on_delete=models.SET_NULL, limit_choices_to={'componentGroup__code': 'PROJECT_STATUS'}, related_name='projectStatus')
    components = models.ManyToManyField(Component, null=True, limit_choices_to={'componentGroup__code': 'PROJECT_COMPONENTS'}, related_name='projectComponents')
    members = models.ManyToManyField(User, blank=True, related_name='projectMembers')
    watchers = models.ManyToManyField(User, blank=True, related_name='projectWatchers')
    icon = models.ImageField(upload_to='project-icons/', default=getRandomProjectIcon)
    isPrivate = models.BooleanField(default=False)
    # TODO: Consider status and resolution foreign key.

    class Meta:
        verbose_name = "Project"
        verbose_name_plural = "Projects"
        index_together = [
            ("internalKey", "code", "url"),
        ]

    def __str__(self):
        return self.internalKey

    def getUrl(self):
        return reverse('jira:issuesListView') + f'?project={self.code}'

    def serializeProjectVersion1(self):
        return {
            "id": self.id or None,
            "internalKey": self.internalKey,
            "code": self.code,
            "icon": self.icon.url,
            "link": self.getUrl(),
        }


class Board(BaseModel):
    class Types(models.TextChoices):
        SCRUM = 'SCRUM', _('Scrum')
        KANBAN = 'KANBAN', _('Kanban')

    internalKey = models.CharField(max_length=2048, blank=True, null=True, unique=True)
    url = models.SlugField(max_length=10, editable=settings.DEBUG, unique=True, default=generateString, db_index=True)
    projects = models.ManyToManyField(Project, blank=True, related_name='boardProjects')
    admins = models.ManyToManyField(User, blank=True, related_name='boardAdmins')
    members = models.ManyToManyField(User, blank=True, related_name='boardMembers')
    type = models.CharField(max_length=10, choices=Types.choices, default=Types.KANBAN)
    isPrivate = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Board"
        verbose_name_plural = "Boards"
        ordering = ['orderNo']

    def __str__(self):
        return self.internalKey

    def getUrl(self):
        return reverse('jira:board-page', kwargs={'url': self.url})

    def hasAccessPermission(self, user):
        if not self.isPrivate:
            return True
        return user in self.members.all() or user in self.admins.all()

    def serializeBoardVersion1(self):
        return {
            "id": self.id or None,
            "internalKey": self.internalKey,
            "url": self.url,
            "type": self.type,
            "link": self.getUrl(),
        }


class Label(BaseModel):
    internalKey = models.CharField(max_length=2048, unique=True)
    code = models.CharField(max_length=2048, unique=True)
    colour = ColorField(default='#FF0000')

    class Meta:
        verbose_name = "Label"
        verbose_name_plural = "Labels"

    def __str__(self):
        return self.internalKey

    def serializeLabelVersion1(self):
        return {
            "id": self.id or None,
            "internalKey": self.internalKey,
            "code": self.code,
            "colour": self.colour,
        }


class Column(BaseModel):
    class Category(models.TextChoices):
        TODO = 'TODO', _('To Do')
        IN_PROGRESS = 'IN_PROGRESS', _('In Progress')
        DONE = 'DONE', _('Done')

    class Colour(models.TextChoices):
        TODO = '#42526e', _('#42526e')
        IN_PROGRESS = '#0052cc', _('#0052cc')
        DONE = '#00875a', _('#00875a')

    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='boardColumns')
    internalKey = models.CharField(max_length=2048)
    category = models.CharField(max_length=16, choices=Category.choices, default=Category.IN_PROGRESS)
    colour = ColorField(default='#FF0000')

    class Meta:
        verbose_name = "Column"
        verbose_name_plural = "Columns"
        ordering = ['orderNo']

    def __str__(self):
        return self.internalKey

    def validate_unique(self, *args, **kwargs):
        # TODO: Need to test this.
        super().validate_unique(*args, **kwargs)
        if self.__class__.objects.filter(id=None, board=self.board, internalKey=self.internalKey).exists():
            raise ValidationError(
                message='Column name for this board already exists.',
                code='unique_together',
            )


class ColumnStatus(BaseModel):
    class Category(models.TextChoices):
        TODO = 'TODO', _('To Do')
        IN_PROGRESS = 'IN_PROGRESS', _('In Progress')
        DONE = 'DONE', _('Done')

    class Colour(models.TextChoices):
        TODO = '#42526e', _('#dfe1e5')
        IN_PROGRESS = '#0052cc', _('#deebff')
        DONE = '#00875a', _('#e3fcef')

    internalKey = models.CharField(max_length=2048)
    board = models.ForeignKey(Board, blank=True, null=True, on_delete=models.CASCADE, related_name="boardColumnStatus")
    column = models.ForeignKey(Column, blank=True, null=True, on_delete=models.CASCADE, related_name="columnStatus")
    setResolution = models.BooleanField(default=False)
    category = models.CharField(max_length=16, choices=Category.choices, default=Category.IN_PROGRESS)
    colour = ColorField(default='#FF0000')

    class Meta:
        verbose_name = "ColumnStatus"
        verbose_name_plural = "ColumnStatus"

    def serializeColumnStatusVersion1(self, **kwargs):
        data = {
            "id": self.id or None,
            "internalKey": self.internalKey,
            "setResolution": self.setResolution,
            "category": self.category,
            "colour": self.colour,
        }
        try:
            mergedData = data | kwargs
        except TypeError:
            mergedData = {**data, **kwargs}
        return mergedData


class Ticket(BaseModel):
    internalKey = models.CharField(max_length=2048, unique=True, db_index=True)  # PROJECT_CODE + PK
    summary = models.CharField(max_length=2048)
    description = models.TextField(blank=True, null=True)
    storyPoints = models.PositiveSmallIntegerField(blank=True, null=True)
    project = models.ForeignKey(Project, on_delete=models.PROTECT, null=True, related_name="projectTickets")
    assignee = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="ticketAssignee")
    reporter = models.ForeignKey(User, on_delete=models.PROTECT, related_name="ticketReporter")
    subTask = models.ManyToManyField('Ticket', blank=True, related_name='ticketSubTask')
    component = models.ManyToManyField(Component, blank=True, related_name="ticketComponents", limit_choices_to={'componentGroup__code': 'PROJECT_COMPONENTS'})
    resolution = models.ForeignKey(Component, on_delete=models.SET_NULL, null=True, related_name="ticketResolutions" , limit_choices_to={'componentGroup__code': 'TICKET_RESOLUTIONS'})
    issueType = models.ForeignKey(Component, on_delete=models.PROTECT, related_name='ticketIssueType', limit_choices_to={'componentGroup__code': 'TICKET_ISSUE_TYPE'})
    priority = models.ForeignKey(Component, on_delete=models.PROTECT, related_name='ticketPriority', limit_choices_to={'componentGroup__code': 'TICKET_PRIORITY'})
    columnStatus = models.ForeignKey(ColumnStatus, blank=True, null=True, on_delete=models.SET_NULL, related_name='columnStatusTickets')
    epic = models.ForeignKey('Ticket', null=True, blank=True, on_delete=models.SET_NULL, related_name='epicTickets', limit_choices_to={'issueType__code': 'EPIC'})

    # advanced columns
    label = models.ManyToManyField(Label, blank=True, related_name='ticketLabels')
    colour = ColorField(default='#FF0000')  # EPIC colour
    watchers = models.ManyToManyField(User, blank=True, related_name='ticketWatchers')
    fixVersion = models.CharField(max_length=2048, blank=True, null=True)
    manDays = models.PositiveSmallIntegerField(blank=True, null=True)

    # board and column attributes should be deprecated
    column = models.ForeignKey(Column, null=True, on_delete=models.SET_NULL, related_name='columnTickets')
    board = models.ForeignKey(Board, blank=True, null=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"

    def __str__(self):
        return self.internalKey

    def getTicketUrl(self):
        return reverse('jira:ticket-detail-view', kwargs={'internalKey': self.internalKey})

    def getEpicUrl(self):
        return reverse('jira:ticket-detail-view', kwargs={'internalKey': self.epic.internalKey})


class TicketAttachment(BaseModel):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='ticketAttachments')
    uploadedBy = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploadedTicketAttachments')
    internalKey = models.CharField(max_length=2048, default=generateString)
    attachment = models.FileField(upload_to='ticket-attachment/', blank=True)

    class Meta:
        verbose_name = "TicketAttachment"
        verbose_name_plural = "TicketAttachments"

    def __str__(self):
        return self.internalKey  # f'{self.ticket} {self.internalKey}'


class TicketComment(BaseModel):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='ticketComments')
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ticketCommentCreator')
    comment = models.TextField()
    edited = models.BooleanField(default=False)
    reply = models.ForeignKey('TicketComment', null=True, blank=True, related_name='replies', on_delete=models.CASCADE)
    likes = models.ManyToManyField(User, related_name='ticketCommentLikes')
    dislikes = models.ManyToManyField(User, related_name='ticketCommentDislikes')

    class Meta:
        verbose_name = "TicketComment"
        verbose_name_plural = "TicketComments"

    def like(self, request):
        if request.user not in self.likes.all():
            self.likes.add(request.user)
        else:
            self.likes.remove(request.user)

        if request.user in self.dislikes.all():
            self.dislikes.remove(request.user)

    def dislike(self, request):
        if request.user not in self.dislikes.all():
            self.dislikes.add(request.user)
        else:
            self.dislikes.remove(request.user)

        if request.user in self.likes.all():
            self.likes.remove(request.user)


class Sprint(BaseModel):
    board = models.ForeignKey(Board, on_delete=models.SET_NULL, blank=True, null=True, related_name='boardSprints')
    internalKey = models.CharField(max_length=2048, blank=True, null=True)
    tickets = models.ManyToManyField(Ticket, related_name='sprintTickets')
    startDate = models.DateField(blank=True, null=True)
    endDate = models.DateField(blank=True, null=True)
    isComplete = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Sprint"
        verbose_name_plural = "Sprints"

    def removeTicketsFromSprint(self, tickets):
        self.tickets.remove(*tickets)

    def addTicketsToSprint(self, tickets):
        self.tickets.add(*tickets)
