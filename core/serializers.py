from django.contrib.auth.models import User
from rest_framework import serializers

from core.models import Project


class ProjectSerializerVersion1(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = [
            'id',
            'name',
            'code',
            'url',
        ]


class UserSerializerVersion1(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'first_name',
            'last_name'
        ]
