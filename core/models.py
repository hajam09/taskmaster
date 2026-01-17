import os
import random
import uuid

from colorfield.fields import ColorField
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


def getRandomAvatar():
    return 'avatars/' + random.choice(os.listdir(os.path.join(settings.MEDIA_ROOT, 'avatars/')))


def getRandomProjectIcon():
    return 'project-icons/' + random.choice(os.listdir(os.path.join(settings.MEDIA_ROOT, 'project-icons/')))


def getRandomString():
    return uuid.uuid4().hex[:8]


class BaseModel(models.Model):
    createdDateTime = models.DateTimeField(default=timezone.now)
    modifiedDateTime = models.DateTimeField(auto_now=True)
    orderNo = models.IntegerField(default=0)

    class Meta:
        abstract = True


class Profile(BaseModel):
    class JobTitle(models.TextChoices):
        SOFTWARE_ENGINEER = 'SOFTWARE_ENGINEER', _('Software Engineer')
        FRONTEND_DEVELOPER = 'FRONTEND_DEVELOPER', _('Frontend Developer')
        BACKEND_DEVELOPER = 'BACKEND_DEVELOPER', _('Backend Developer')
        DEVOPS_ENGINEER = 'DEVOPS_ENGINEER', _('DevOps Engineer')
        QA_ENGINEER = 'QA_ENGINEER', _('QA Engineer')
        PROJECT_OWNER = 'PROJECT_OWNER', _('Project Owner')
        PROJECT_MANAGER = 'PROJECT_MANAGER', _('Project Manager')
        SCRUM_MASTER = 'SCRUM_MASTER', _('Scrum Master')
        UX_UI_DESIGNER = 'UX_UI_DESIGNER', _('UX/UI Designer')
        SOLUTIONS_ARCHITECT = 'SOLUTIONS_ARCHITECT', _('Solutions Architect')
        BUSINESS_ANALYST = 'BUSINESS_ANALYST', _('Business Analyst')
        PRODUCT_MANAGER = 'PRODUCT_MANAGER', _('Product Manager')
        DATA_SCIENTIST = 'DATA_SCIENTIST', _('Data Scientist')
        INTERN = 'INTERN', _('Intern')

    user = models.OneToOneField(User, on_delete=models.DO_NOTHING, related_name='profile')
    url = models.CharField(max_length=8, editable=False, unique=True, default=getRandomString)
    jobTitle = models.CharField(max_length=32, blank=True, null=True, choices=JobTitle.choices)
    department = models.CharField(max_length=128, blank=True, null=True)

    # icon = models.ImageField(upload_to='profile-picture', blank=True, null=True, default=getRandomAvatar)

    class Meta:
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'

    def __str__(self):
        return self.user.get_full_name()


class Team(BaseModel):
    name = models.CharField(max_length=128, unique=True)
    url = models.CharField(max_length=8, editable=False, unique=True, default=getRandomString)
    description = models.TextField()
    isPrivate = models.BooleanField(default=False)
    admins = models.ManyToManyField(User, blank=True, related_name='teamAdmins')
    members = models.ManyToManyField(User, blank=True, related_name='teamMembers')

    class Meta:
        verbose_name = 'Team'
        verbose_name_plural = 'Teams'

    def __str__(self):
        return self.name

    def hasViewPermission(self, user):
        if not self.isPrivate:
            return True
        return user in self.members.all() or user in self.admins.all()


class Project(BaseModel):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', _('Active')
        IN_PROGRESS = 'IN_PROGRESS', _('In Progress')
        ON_HOLD = 'ON_HOLD', _('On Hold')
        COMPLETED = 'COMPLETED', _('Completed')
        CANCELLED = 'CANCELLED', _('Cancelled')
        TERMINATED = 'TERMINATED', _('Terminated')
        DRAFT = 'DRAFT', _('Draft')
        INACTIVE = 'INACTIVE', _('Inactive')
        PENDING = 'PENDING', _('Pending')
        ARCHIVED = 'ARCHIVED', _('Archived')
        DELAYED = 'DELAYED', _('Delayed')
        APPROVED = 'APPROVED', _('Approved')
        REJECTED = 'REJECTED', _('Rejected')
        WAITING_FOR_FEEDBACK = 'WAITING_FOR_FEEDBACK', _('Waiting for Feedback')
        UNDER_REVIEW = 'UNDER_REVIEW', _('Under Review')
        READY_FOR_REVIEW = 'READY_FOR_REVIEW', _('Ready for Review')

    name = models.CharField(max_length=128, unique=True)
    code = models.CharField(max_length=8, unique=True)
    url = models.CharField(max_length=8, editable=False, unique=True, default=getRandomString)
    description = models.TextField()
    startDate = models.DateField(default=timezone.now)
    endDate = models.DateField(default=timezone.datetime.max)
    status = models.CharField(max_length=32, blank=True, null=True, choices=Status.choices)
    isPrivate = models.BooleanField(default=False)
    lead = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    members = models.ManyToManyField(User, blank=True, related_name='projectMembers')

    # icon = models.ImageField(upload_to='project-icons/', default=getRandomProjectIcon)

    class Meta:
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'

    def __str__(self):
        return self.name

    def hasViewPermission(self, user):
        if not self.isPrivate:
            return True
        return user == self.lead or user in self.members.all()


class Board(BaseModel):
    class Types(models.TextChoices):
        SCRUM = 'SCRUM', _('Scrum')
        KANBAN = 'KANBAN', _('Kanban')

    name = models.CharField(max_length=128, unique=True)
    url = models.CharField(max_length=8, editable=False, unique=True, default=getRandomString)
    type = models.CharField(max_length=8, choices=Types.choices, default=Types.KANBAN)
    isPrivate = models.BooleanField(default=False)
    project = models.ForeignKey(Project, on_delete=models.DO_NOTHING, related_name='boardProjects')
    admins = models.ManyToManyField(User, blank=True, related_name='boardAdmins')
    members = models.ManyToManyField(User, blank=True, related_name='boardMembers')

    class Meta:
        verbose_name = 'Board'
        verbose_name_plural = 'Boards'

    def __str__(self):
        return self.name

    def hasViewPermission(self, user):
        if not self.isPrivate:
            return True
        return user in self.members.all() or user in self.admins.all()

    @property
    def getUrl(self):
        return reverse('core:board-view', kwargs={'url': self.url})


class Label(BaseModel):
    name = models.CharField(max_length=128, unique=True)
    code = models.CharField(max_length=128, unique=True)
    url = models.CharField(max_length=8, editable=False, unique=True, default=getRandomString)
    colour = ColorField(default='#000000')

    class Meta:
        verbose_name = 'Label'
        verbose_name_plural = 'Labels'

    def __str__(self):
        return self.name


class Column(BaseModel):
    class Status(models.TextChoices):
        UNMAPPED = 'UNMAPPED', _('Unmapped')
        BACK_LOG = 'BACK_LOG', _('Back Log')
        TODO = 'TODO', _('To Do')
        IN_PROGRESS = 'IN_PROGRESS', _('In Progress')
        DONE = 'DONE', _('Done')

    name = models.CharField(max_length=32)
    board = models.ForeignKey(Board, on_delete=models.DO_NOTHING, related_name='boardColumns')
    status = models.CharField(max_length=16, blank=True, null=True, choices=Status.choices)

    class Meta:
        verbose_name = 'Column'
        verbose_name_plural = 'Columns'
        ordering = ['orderNo']

    def __str__(self):
        return self.name

    def getColour(self):
        if self.status == self.Status.UNMAPPED:
            return '#42526E'
        elif self.status == self.Status.BACK_LOG:
            return '#42526E'
        elif self.status == self.Status.TODO:
            return '#42526E'
        elif self.status == self.Status.IN_PROGRESS:
            return '#0052CC'
        elif self.status == self.Status.DONE:
            return '#00875A'
        raise NotImplemented

    def save(self, *args, **kwargs):
        isNew = self.pk is None
        super().save(*args, **kwargs)

        if isNew:
            self.orderNo = self.pk
            super().save(update_fields=['orderNo'])


class ColumnStatus(BaseModel):
    name = models.CharField(max_length=32)
    column = models.ForeignKey(Column, on_delete=models.DO_NOTHING, related_name='columnStatus')

    class Meta:
        verbose_name = 'ColumnStatus'
        verbose_name_plural = 'ColumnStatus'
        ordering = ['orderNo']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        isNew = self.pk is None
        super().save(*args, **kwargs)

        if isNew:
            self.orderNo = self.pk
            super().save(update_fields=['orderNo'])


class Ticket(BaseModel):
    class Resolution(models.TextChoices):
        UNRESOLVED = 'UNRESOLVED', _('Unresolved')  # Default, unresolved state
        FIXED = 'FIXED', _('Fixed')  # Issue has been resolved via a fix
        WONT_FIX = 'WONT_FIX', _('Won\'t Fix')  # Valid issue, but won’t be addressed
        DUPLICATE = 'DUPLICATE', _('Duplicate')  # Same as another ticket
        INCOMPLETE = 'INCOMPLETE', _('Incomplete')  # Not enough info to act
        CANNOT_REPRODUCE = 'CANNOT_REPRODUCE', _('Cannot Reproduce')  # Could not replicate issue
        NOT_A_BUG = 'NOT_A_BUG', _('Not a Bug')  # Intended behavior or non-defect
        POSTPONED = 'POSTPONED', _('Postponed')  # Deferred for future
        RESOLVED = 'RESOLVED', _('Resolved')  # General “done” status
        CLOSED = 'CLOSED', _('Closed')  # Explicitly marked as done, with or without fix
        REOPENED = 'REOPENED', _('Reopened')  # Issue reoccurred or wrongly resolved

    class Type(models.TextChoices):
        BUG = 'BUG', _('Bug')
        EPIC = 'EPIC', _('Epic')
        STORY = 'STORY', _('Story')
        SUB_TASK = 'SUB_TASK', _('Sub Task')
        TASK = 'TASK', _('Task')
        TEST = 'TEST', _('Test')
        SPIKE = 'SPIKE', _('Spike')

    class Priority(models.TextChoices):
        BLOCKER = 'BLOCKER', _('Blocker')
        CRITICAL = 'CRITICAL', _('Critical')
        HIGH = 'HIGH', _('High')
        HIGHEST = 'HIGHEST', _('Highest')
        LOW = 'LOW', _('Low')
        LOWEST = 'LOWEST', _('Lowest')
        MAJOR = 'MAJOR', _('Major')
        MEDIUM = 'MEDIUM', _('Medium')
        MINOR = 'MINOR', _('Minor')
        TRIVIAL = 'TRIVIAL', _('Trivial')

    class LinkType(models.TextChoices):
        LINKED_TO_ACTION = 'LINKED_TO_ACTION', _('linked to action')
        LINKED_FROM_ACTION = 'LINKED_FROM_ACTION', _('linked from action')
        BLOCKS = 'BLOCKS', _('blocks')
        IS_BLOCKED_BY = 'IS_BLOCKED_BY', _('is blocked by')
        IS_A_CHANGE_TO = 'IS_A_CHANGE_TO', _('Is a change to')
        CHANGED_BY = 'CHANGED_BY', _('changed by')
        CLONES = 'CLONES', _('clones')
        IS_CLONED_BY = 'IS_CLONED_BY', _('is cloned by')
        IS_DEPENDENT_ON = 'IS_DEPENDENT_ON', _('is dependent on')
        IS_DEPENDENCY_OF = 'IS_DEPENDENCY_OF', _('is dependency of')
        DUPLICATED = 'DUPLICATED', _('duplicates')
        IS_DUPLICATED_BY = 'IS_DUPLICATED_BY', _('is duplicated by')
        IMPACTS = 'IMPACTS', _('impacts')
        IMPACTED_BY = 'IMPACTED_BY', _('impacted by')
        REPLACES = 'REPLACES', _('replaces')
        IS_REPLACED_BY = 'IS_REPLACED_BY', _('is replaced by')
        LINKED_TO_RISK = 'LINKED_TO_RISK', _('linked to risk')
        LINKED_FROM_RISK = 'LINKED_FROM_RISK', _('linked from risk')
        CAUSES = 'CAUSES', _('causes')
        IS_CAUSED_BY = 'IS_CAUSED_BY', _('is caused by')
        CONTAINS = 'CONTAINS', _('contains')
        CONTRIBUTES_TO = 'CONTRIBUTES_TO', _('contributes to')
        FULLY_IMPLEMENTS = 'FULLY_IMPLEMENTS', _('fully implements')
        IS_FULLY_IMPLEMENTED_BY = 'IS_FULLY_IMPLEMENTED_BY', _('is fully implemented by')
        RELATES = 'RELATES', _('relates')
        IS_RELATED_BY = 'IS_RELATED_BY', _('is related by')
        PARTIALLY_IMPLEMENTS = 'PARTIALLY_IMPLEMENTS', _('partially implements')
        IS_PARTIALLY_IMPLEMENTED_BY = 'IS_PARTIALLY_IMPLEMENTED_BY', _('is partially implemented by')
        STARTS_WITH = 'STARTS_WITH', _('starts with')
        FINISHES_WITH = 'FINISHES_WITH', _('finishes with')
        HAS_TO_BE_DONE_BEFORE = 'HAS_TO_BE_DONE_BEFORE', _('has to be done before')
        HAS_TO_BE_DONE_AFTER = 'HAS_TO_BE_DONE_AFTER', _('has to be done after')
        HAS_TO_BE_STARTED_TOGETHER_WITH = 'HAS_TO_BE_STARTED_TOGETHER_WITH', _('has to be started together with')
        HAS_TO_BE_FINISHED_TOGETHER_WITH = 'HAS_TO_BE_FINISHED_TOGETHER_WITH', _('has to be finished together with')
        IS_PARENT_TASK_OF = 'IS_PARENT_TASK_OF', _('is parent task of')
        IS_SUBTASK_OK = 'IS_SUBTASK_OK', _('is subtask of')

    url = models.CharField(max_length=32, unique=True)
    summary = models.CharField(max_length=2048)
    description = models.TextField(blank=True, null=True)
    storyPoints = models.PositiveSmallIntegerField(blank=True, null=True)
    resolution = models.CharField(max_length=16, blank=True, null=True, choices=Resolution.choices)
    type = models.CharField(max_length=8, blank=True, null=True, choices=Type.choices)
    priority = models.CharField(max_length=8, blank=True, null=True, choices=Priority.choices)
    colour = ColorField(default='#FF0000')

    project = models.ForeignKey(Project, on_delete=models.DO_NOTHING, related_name='projectTickets')
    assignee = models.ForeignKey(User, null=True, blank=True, on_delete=models.DO_NOTHING)
    reporter = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='ticketReporter')
    columnStatus = models.ForeignKey(ColumnStatus, on_delete=models.DO_NOTHING, related_name='columnStatusTickets')
    subTask = models.ManyToManyField('Ticket', blank=True, related_name='ticketSubTask')
    label = models.ManyToManyField(Label, blank=True, related_name='ticketLabels')
    watchers = models.ManyToManyField(User, blank=True, related_name='ticketWatchers')

    epic = models.ForeignKey(
        'Ticket',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='epicTickets',
        limit_choices_to={'type': 'EPIC'}
    )

    linkType = models.CharField(max_length=64, blank=True, null=True, choices=LinkType.choices)
    linkedIssues = models.ManyToManyField('Ticket', blank=True, related_name='ticketLinkedIssues')

    class Meta:
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'
        ordering = ['orderNo']

    icons = {
        Type.BUG: 'https://cdn-thumbs.imagevenue.com/76/05/cc/ME14ZPM0_t.jpg',
        Type.EPIC: 'https://cdn-thumbs.imagevenue.com/e9/21/f5/ME14ZPM1_t.jpg',
        Type.STORY: 'https://cdn-thumbs.imagevenue.com/cc/5e/08/ME14ZPM6_t.jpg',
        Type.SUB_TASK: 'https://cdn-thumbs.imagevenue.com/9c/bb/4c/ME14ZPM8_t.jpg',
        Type.TASK: 'https://cdn-thumbs.imagevenue.com/d1/5c/cd/ME14ZPM9_t.jpg',
        Type.TEST: 'https://cdn-thumbs.imagevenue.com/45/69/8d/ME14ZPMA_t.jpg',
        Type.SPIKE: 'https://cdn-thumbs.imagevenue.com/90/63/63/ME14ZPM4_t.jpg',
        Priority.BLOCKER: 'https://raw.githubusercontent.com/cglynne/jira-priority-icons/dc505157ab8cdac2adad074ef054da783f9fee70/jira_priority/blocker.svg',
        Priority.CRITICAL: 'https://raw.githubusercontent.com/cglynne/jira-priority-icons/dc505157ab8cdac2adad074ef054da783f9fee70/jira_priority/critical.svg',
        Priority.HIGH: 'https://raw.githubusercontent.com/cglynne/jira-priority-icons/dc505157ab8cdac2adad074ef054da783f9fee70/jira_priority/high.svg',
        Priority.HIGHEST: 'https://raw.githubusercontent.com/cglynne/jira-priority-icons/dc505157ab8cdac2adad074ef054da783f9fee70/jira_priority/highest.svg',
        Priority.LOW: 'https://raw.githubusercontent.com/cglynne/jira-priority-icons/dc505157ab8cdac2adad074ef054da783f9fee70/jira_priority/low.svg',
        Priority.LOWEST: 'https://raw.githubusercontent.com/cglynne/jira-priority-icons/dc505157ab8cdac2adad074ef054da783f9fee70/jira_priority/lowest.svg',
        Priority.MAJOR: 'https://raw.githubusercontent.com/cglynne/jira-priority-icons/dc505157ab8cdac2adad074ef054da783f9fee70/jira_priority/major.svg',
        Priority.MEDIUM: 'https://raw.githubusercontent.com/cglynne/jira-priority-icons/dc505157ab8cdac2adad074ef054da783f9fee70/jira_priority/medium.svg',
        Priority.MINOR: 'https://raw.githubusercontent.com/cglynne/jira-priority-icons/dc505157ab8cdac2adad074ef054da783f9fee70/jira_priority/minor.svg',
        Priority.TRIVIAL: 'https://raw.githubusercontent.com/cglynne/jira-priority-icons/dc505157ab8cdac2adad074ef054da783f9fee70/jira_priority/trivial.svg',
    }

    @property
    def ticketTypeIcon(self):
        return self.icons.get(self.type)

    @property
    def ticketPriorityIcon(self):
        return self.icons.get(self.priority)

    @property
    def getUrl(self):
        return reverse('core:ticket-view', kwargs={'url': self.url})

    @property
    def getIcon(self):
        return "https://dummyimage.com/100x100/"

    def __str__(self):
        return self.url

    def save(self, *args, **kwargs):
        isNew = self.pk is None
        super().save(*args, **kwargs)

        if isNew:
            self.orderNo = self.pk
            super().save(update_fields=['orderNo'])

    def delete(self, *args, **kwargs):
        Ticket.objects.filter(epic=self).update(epic=None)
        super().delete(*args, **kwargs)


#
#
# class TicketAttachment(BaseModel):
#     ticket = models.ForeignKey(Ticket, on_delete=models.DO_NOTHING, related_name='ticketAttachments')
#     uploadedBy = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='uploadedTicketAttachments')
#     internalKey = models.CharField(max_length=128, default=getRandomString)
#     attachment = models.FileField(upload_to='ticket-attachment/', blank=True)
#
#     class Meta:
#         verbose_name = 'TicketAttachment'
#         verbose_name_plural = 'TicketAttachments'
#
#     def __str__(self):
#         return self.internalKey
#
#
# class TicketComment(BaseModel):
#     ticket = models.ForeignKey(Ticket, on_delete=models.DO_NOTHING, related_name='ticketComments')
#     creator = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='ticketCommentCreator')
#     comment = models.TextField()
#     edited = models.BooleanField(default=False)
#     likes = models.ManyToManyField(User, blank=True, related_name='ticketCommentLikes')
#     dislikes = models.ManyToManyField(User, blank=True, related_name='ticketCommentDislikes')
#
#     class Meta:
#         verbose_name = 'TicketComment'
#         verbose_name_plural = 'TicketComments'
#
#     def like(self, request):
#         if request.user not in self.likes.all():
#             self.likes.add(request.user)
#         else:
#             self.likes.remove(request.user)
#
#         if request.user in self.dislikes.all():
#             self.dislikes.remove(request.user)
#
#     def dislike(self, request):
#         if request.user not in self.dislikes.all():
#             self.dislikes.add(request.user)
#         else:
#             self.dislikes.remove(request.user)
#
#         if request.user in self.likes.all():
#             self.likes.remove(request.user)
#
#


class Sprint(BaseModel):
    board = models.ForeignKey(Board, on_delete=models.DO_NOTHING, related_name='boardSprints')
    name = models.CharField(max_length=128, unique=True)
    tickets = models.ManyToManyField(Ticket, related_name='sprintTickets', blank=True)
    goal = models.TextField(blank=True, null=True)
    startDate = models.DateField(blank=True, null=True)
    endDate = models.DateField(blank=True, null=True)
    isComplete = models.BooleanField(default=False)
    isActive = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Sprint'
        verbose_name_plural = 'Sprints'

    def __str__(self):
        return self.name
