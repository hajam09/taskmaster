import bleach
from django.contrib.auth.models import User
from django.db.models import Max
from rest_framework import serializers

from core import service
from core.models import Column, ColumnStatus, Label, Project, Ticket, TicketComment, TicketLink, Board

MAN_AVATAR = 'https://cdn3.iconfinder.com/data/icons/avatars-round-flat/33/man5-512.png'


class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = ['id', 'name', 'colour']


class ColumnSerializer(serializers.ModelSerializer):
    colour = serializers.CharField(source='getColour', read_only=True)

    class Meta:
        model = Column
        fields = ['id', 'name', 'status', 'colour']


class ColumnStatusSerializer(serializers.ModelSerializer):
    column = ColumnSerializer(read_only=True)

    class Meta:
        model = ColumnStatus
        fields = ['id', 'name', 'column']


class UserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='get_full_name', read_only=True)
    icon = serializers.SerializerMethodField()

    def get_icon(self, user):
        return MAN_AVATAR

    class Meta:
        model = User
        fields = ['id', 'name', 'icon']


class ProjectSerializer(serializers.ModelSerializer):
    icon = serializers.CharField(read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'name', 'code', 'url', 'icon']


class BoardSerializer(serializers.ModelSerializer):
    href = serializers.CharField(source='getUrl', read_only=True)

    class Meta:
        model = Board
        fields = ['id', 'name', 'url', 'href', 'type', 'isPrivate']


class TicketSerializerVersion1(serializers.ModelSerializer):
    href = serializers.CharField(source='getUrl', read_only=True)
    description = serializers.SerializerMethodField()
    project = ProjectSerializer(read_only=True)
    type = serializers.SerializerMethodField()
    priority = serializers.SerializerMethodField()
    resolution = serializers.SerializerMethodField()
    reporter = UserSerializer(read_only=True)
    assignee = UserSerializer(allow_null=True)
    epic = serializers.SerializerMethodField()
    parent = serializers.SerializerMethodField()
    label = LabelSerializer(many=True)
    board = BoardSerializer(read_only=True, source='columnStatus.column.board')
    columnStatus = ColumnStatusSerializer(read_only=True)

    def get_description(self, ticket):
        return service.sanitiseTicketDescription(ticket.description)

    def get_type(self, ticket):
        return {
            'key': ticket.type,
            'value': ticket.get_type_display(),
            'icon': ticket.typeIcon,
        }

    def get_priority(self, ticket):
        return {
            'key': ticket.priority,
            'value': ticket.get_priority_display(),
            'icon': ticket.priorityIcon,
        }

    def get_resolution(self, ticket):
        return {
            'key': ticket.resolution,
            'value': ticket.get_resolution_display(),
        }

    def get_epic(self, ticket):
        if ticket.epic:
            return {
                'id': ticket.epic.id,
                'url': ticket.epic.url,
                'href': ticket.epic.getUrl,
                'summary': ticket.epic.summary,
                'icon': ticket.epic.typeIcon,
            }
        return None

    def get_parent(self, ticket):
        if ticket.parent:
            return {
                'id': ticket.parent.id,
                'url': ticket.parent.url,
                'href': ticket.parent.getUrl,
                'summary': ticket.parent.summary,
                'icon': ticket.parent.typeIcon,
            }
        return None

    class Meta:
        model = Ticket
        fields = [
            'id', 'url', 'href', 'summary', 'description', 'storyPoints', 'createdDateTime', 'modifiedDateTime', 'type',
            'priority', 'project', 'reporter', 'assignee', 'resolution', 'epic', 'parent', 'label', 'board',
            'columnStatus',
        ]


class TicketSerializerVersion2(serializers.ModelSerializer):
    href = serializers.CharField(source='getUrl', read_only=True)
    type = serializers.SerializerMethodField()
    priority = serializers.SerializerMethodField()
    columnStatus = ColumnStatusSerializer(read_only=True)
    isDone = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = ['id', 'url', 'href', 'summary', 'storyPoints', 'priority', 'type', 'isDone', 'columnStatus']

    def get_isDone(self, ticket):
        return ticket.columnStatus.column.status == Column.Status.DONE

    def get_type(self, ticket):
        return {
            'key': ticket.type,
            'value': ticket.get_type_display(),
            'icon': ticket.typeIcon,
        }

    def get_priority(self, ticket):
        return {
            'key': ticket.priority,
            'value': ticket.get_priority_display(),
            'icon': ticket.priorityIcon,
        }


class SubTaskTicketCreateSerializer(serializers.Serializer):
    summary = serializers.CharField(max_length=2048, allow_blank=False, trim_whitespace=True)

    def create(self, validated_data):
        parent = self.context['ticket']
        project = parent.project
        maxOrderNo = Ticket.objects.filter(project=project).aggregate(maxOrderNo=Max('orderNo'))['maxOrderNo'] or 0
        subtask = Ticket.objects.create(
            url=f'{project.code}-{maxOrderNo + 1}',
            summary=validated_data['summary'],
            type=Ticket.Type.SUB_TASK,
            priority=parent.priority,
            project=project,
            reporter=self.context['request'].user,
            columnStatus=parent.columnStatus,
            parent=parent
        )
        return subtask


class EpicTicketCreateSerializer(serializers.Serializer):
    summary = serializers.CharField(max_length=2048, allow_blank=False, trim_whitespace=True)

    def create(self, validated_data):
        epic = self.context['ticket']
        project = epic.project
        maxOrderNo = Ticket.objects.filter(project=project).aggregate(maxOrderNo=Max('orderNo'))['maxOrderNo'] or 0
        return Ticket.objects.create(
            url=f'{project.code}-{maxOrderNo + 1}',
            summary=validated_data['summary'],
            type=Ticket.Type.STORY,
            priority=epic.priority,
            project=project,
            reporter=self.context['request'].user,
            columnStatus=epic.columnStatus,
            epic=epic,
        )


class SubTaskTicketAttachSerializer(serializers.Serializer):
    ticketIds = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=False)


class EpicTicketAttachSerializer(serializers.Serializer):
    ticketIds = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=False)


class TicketLinkCreateSerializer(serializers.Serializer):
    linkType = serializers.ChoiceField(choices=TicketLink.LinkType.choices)
    ticketIds = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=False)


class TicketUpdateSerializer(serializers.ModelSerializer):
    label = serializers.ListField(child=serializers.IntegerField(min_value=1), required=False, allow_empty=True)

    class Meta:
        model = Ticket
        fields = [
            'summary', 'description', 'storyPoints', 'resolution', 'type', 'priority', 'assignee', 'columnStatus',
            'label', 'parent', 'epic'
        ]

    def validate_columnStatus(self, columnStatus):
        if columnStatus is not None and self.instance.columnStatus.column.board_id != columnStatus.column.board_id:
            raise serializers.ValidationError('Column status must belong to the same board as the ticket.')
        return columnStatus

    def validate_label(self, labelIds):
        return list(Label.objects.filter(pk__in=labelIds))


class TicketCommentSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    ticket = serializers.PrimaryKeyRelatedField(read_only=True)
    comment = serializers.CharField()
    createdDateTime = serializers.DateTimeField(read_only=True)
    inLikes = serializers.BooleanField(source='in_likes', read_only=True, default=False)
    inDisLikes = serializers.BooleanField(source='in_dislikes', read_only=True, default=False)
    likesCount = serializers.IntegerField(source='likes_count', read_only=True, default=0)
    disLikesCount = serializers.IntegerField(source='dislikes_count', read_only=True, default=0)

    class Meta:
        model = TicketComment
        fields = [
            'id', 'ticket', 'creator', 'comment', 'edited', 'createdDateTime', 'inLikes', 'inDisLikes', 'likesCount',
            'disLikesCount'
        ]

    def validate_comment(self, comment):
        sanitized = service.sanitiseTicketDescription(comment)
        if not bleach.clean(sanitized, tags=[], strip=True).strip():
            raise serializers.ValidationError('A comment cannot be empty.')
        return sanitized

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['comment'] = service.sanitiseTicketDescription(representation['comment'])
        return representation
