from django.contrib import admin

from core.models import (
    Profile,
    Team,
    Project,
    Board,
    Label,
    Column,
    ColumnStatus,
    Ticket,
    Sprint
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
    list_display = ('id', 'name', 'orderNo')


@admin.register(ColumnStatus)
class ColumnStatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'orderNo')


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'url', 'type', 'orderNo')
    filter_horizontal = (
        'subTask',
        'label',
        'watchers',
        'linkedIssues',
    )

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name in ['subTask', 'linkedIssues']:
            if request._obj_ is not None:
                kwargs['queryset'] = Ticket.objects.exclude(pk=request._obj_.pk)
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def get_form(self, request, obj=None, **kwargs):
        request._obj_ = obj
        return super().get_form(request, obj, **kwargs)


@admin.register(Sprint)
class SprintAdmin(admin.ModelAdmin):
    pass
