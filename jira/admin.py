from django.contrib import admin

from jira.models import Board
from jira.models import Column
from jira.models import ColumnStatus
from jira.models import Label
from jira.models import Project
from jira.models import Sprint
from jira.models import Ticket
from jira.models import TicketAttachment
from jira.models import TicketComment

admin.site.register(Board)
admin.site.register(Column)
admin.site.register(ColumnStatus)
admin.site.register(Label)
admin.site.register(Project)
admin.site.register(Sprint)
admin.site.register(Ticket)
admin.site.register(TicketAttachment)
admin.site.register(TicketComment)
