import bleach
from django.contrib.auth.models import User
from rest_framework import serializers

from core.models import ColumnStatus, Label, Project, Ticket, TicketComment

DESCRIPTION_TAGS = [
    'a', 'blockquote', 'br', 'code', 'em', 'h1', 'h2', 'h3', 'i', 'li',
    'ol', 'p', 'pre', 's', 'strong', 'u', 'ul',
]


def sanitize_ticket_description(description):
    if description is None:
        return ''
    return bleach.clean(
        description,
        tags=DESCRIPTION_TAGS,
        attributes={'a': ['href', 'title']},
        protocols=['http', 'https', 'mailto'],
        strip=True,
    )


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
        return sanitize_ticket_description(ticket.description)

    class Meta:
        model = Ticket
        fields = [
            'id', 'url', 'href', 'summary', 'description', 'storyPoints', 'createdDateTime', 'modifiedDateTime',
            'project',
        ]


class TicketInlineUpdateSerializer(serializers.ModelSerializer):
    assignee = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        allow_null=True,
        required=False,
    )
    columnStatus = serializers.PrimaryKeyRelatedField(
        queryset=ColumnStatus.objects.none(),
        required=False,
    )
    label = serializers.PrimaryKeyRelatedField(
        queryset=Label.objects.all(),
        many=True,
        required=False,
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
        ]

    def validate_description(self, description):
        return sanitize_ticket_description(description)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance is not None:
            self.fields['columnStatus'].queryset = ColumnStatus.objects.filter(
                column__board_id=self.instance.columnStatus.column.board_id
            )


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
        ]
        read_only_fields = [
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
        ]


class TicketCommentSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    ticket = serializers.PrimaryKeyRelatedField(read_only=True)
    comment = serializers.CharField()
    createdDateTime = serializers.DateTimeField(read_only=True)

    inLikes = serializers.BooleanField(
        source='in_likes',
        read_only=True,
        default=False,
    )

    inDisLikes = serializers.BooleanField(
        source='in_dislikes',
        read_only=True,
        default=False,
    )

    likesCount = serializers.IntegerField(
        source='likes_count',
        read_only=True,
        default=0,
    )

    disLikesCount = serializers.IntegerField(
        source='dislikes_count',
        read_only=True,
        default=0,
    )

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
        sanitized = sanitize_ticket_description(comment)
        if not bleach.clean(sanitized, tags=[], strip=True).strip():
            raise serializers.ValidationError('A comment cannot be empty.')
        return sanitized

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['comment'] = sanitize_ticket_description(representation['comment'])
        return representation
