import bleach
from django.contrib.auth.models import User
from django.db.models import Max
from rest_framework import serializers

from core import service
from core.models import Column, ColumnStatus, Label, Project, Ticket, TicketComment, TicketLink

DESCRIPTION_TAGS = [
    'a', 'blockquote', 'br', 'code', 'em', 'h1', 'h2', 'h3', 'i', 'li',
    'ol', 'p', 'pre', 's', 'strong', 'u', 'ul',
]


class ProjectSerializer(serializers.ModelSerializer):
    icon = serializers.SerializerMethodField()

    def get_icon(self, project):
        return project.icon

    class Meta:
        model = Project
        fields = ['id', 'name', 'code', 'url', 'icon']


class TicketSerializerVersion1(serializers.ModelSerializer):
    href = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    project = ProjectSerializer(read_only=True)

    def get_href(self, ticket):
        return ticket.getUrl

    def get_description(self, ticket):
        return service.sanitiseTicketDescription(ticket.description)

    class Meta:
        model = Ticket
        fields = [
            'id', 'url', 'href', 'summary', 'description', 'storyPoints', 'createdDateTime', 'modifiedDateTime',
            'project',
        ]


class TicketSubTaskSerializer(serializers.ModelSerializer):
    href = serializers.CharField(source='getUrl', read_only=True)
    typeIcon = serializers.CharField(source='ticketTypeIcon', read_only=True, allow_null=True)
    priorityIcon = serializers.CharField(source='ticketPriorityIcon', read_only=True, allow_null=True)
    typeDisplay = serializers.CharField(source='get_type_display', read_only=True)
    priorityDisplay = serializers.CharField(source='get_priority_display', read_only=True)
    statusName = serializers.CharField(source='columnStatus.name', read_only=True)
    isDone = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = [
            'id', 'url', 'href', 'summary', 'storyPoints', 'typeIcon', 'priorityIcon',
            'typeDisplay', 'priorityDisplay', 'statusName', 'isDone',
        ]

    def get_isDone(self, ticket):
        return ticket.columnStatus.column.status == Column.Status.DONE


class TicketSubTaskCreateSerializer(serializers.Serializer):
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


class TicketSubTaskAttachSerializer(serializers.Serializer):
    ticketIds = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=False)


class EpicIssueCreateSerializer(serializers.Serializer):
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


class EpicIssueAttachSerializer(serializers.Serializer):
    ticketIds = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=False)


class TicketLinkCreateSerializer(serializers.Serializer):
    linkType = serializers.ChoiceField(choices=TicketLink.LinkType.choices)
    ticketIds = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=False)


class TicketInlineUpdateSerializer(serializers.ModelSerializer):
    assignee = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), allow_null=True, required=False)
    columnStatus = serializers.PrimaryKeyRelatedField(queryset=ColumnStatus.objects.none(), required=False)
    label = serializers.PrimaryKeyRelatedField(queryset=Label.objects.all(), many=True, required=False)
    epic = serializers.PrimaryKeyRelatedField(
        queryset=Ticket.objects.filter(type=Ticket.Type.EPIC),
        allow_null=True,
        required=False
    )

    class Meta:
        model = Ticket
        fields = [
            'summary',
            'description',
            'storyPoints',
            'type',
            'priority',
            'assignee',
            'columnStatus',
            'resolution',
            'label',
            'epic',
        ]

    def validate_description(self, description):
        return service.sanitiseTicketDescription(description)

    def validate_epic(self, epic):
        if epic is not None and epic == self.instance:
            raise serializers.ValidationError('A ticket cannot be its own epic.')
        return epic

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance is not None:
            self.fields['columnStatus'].queryset = ColumnStatus.objects.filter(
                column__board_id=self.instance.columnStatus.column.board_id
            )


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['id', 'username', 'first_name', 'last_name', 'email']


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
            'id',
            'ticket',
            'creator',
            'comment',
            'edited',
            'createdDateTime',
            'inLikes',
            'inDisLikes',
            'likesCount',
            'disLikesCount',
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
