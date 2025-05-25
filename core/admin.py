from django.contrib import admin

from core.models import (
    Profile,
    Team,
    Project,
    Board,
    Label,
    Column,
    ColumnStatus,
    Ticket
)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    pass


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    filter_horizontal = ('admins', 'members')


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    filter_horizontal = ('members',)


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    filter_horizontal = ('admins', 'members')


@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    pass


@admin.register(Column)
class ColumnAdmin(admin.ModelAdmin):
    pass


@admin.register(ColumnStatus)
class ColumnStatusAdmin(admin.ModelAdmin):
    pass


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    pass
