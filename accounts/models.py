import os
import random
import string

from colorfield.fields import ColorField
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


def getRandomAvatar():
    return "avatars/" + random.choice(os.listdir(os.path.join(settings.MEDIA_ROOT, "avatars/")))


def generateString():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))


class BaseModelManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleteFl=False)


class BaseModel(models.Model):
    createdDttm = models.DateTimeField(default=timezone.now)
    modifiedDttm = models.DateTimeField(auto_now=True)
    reference = models.CharField(max_length=2048, blank=True, null=True)
    deleteFl = models.BooleanField(default=False)
    orderNo = models.IntegerField(default=1, blank=True, null=True)
    versionNo = models.IntegerField(default=1, blank=True, null=True)

    object = BaseModelManager()

    class Meta:
        abstract = True


class ComponentGroup(BaseModel):
    internalKey = models.CharField(max_length=2048, blank=True, null=True, unique=True)
    code = models.CharField(max_length=2048, blank=True, null=True)
    icon = models.CharField(max_length=2048, blank=True, null=True)
    colour = ColorField(default='#FF0000')

    class Meta:
        verbose_name = "ComponentGroup"
        verbose_name_plural = "ComponentGroups"

    def __str__(self):
        return self.internalKey

    def getRelatedComponentsByOrderNo(self):
        return self.components.all().order_by('orderNo')


class Component(BaseModel):
    componentGroup = models.ForeignKey(ComponentGroup, on_delete=models.CASCADE, related_name="components")
    internalKey = models.CharField(max_length=2048, blank=True, null=True)
    code = models.CharField(max_length=2048, blank=True, null=True)
    icon = models.CharField(max_length=2048, blank=True, null=True)
    colour = ColorField(default='#FF0000')

    class Meta:
        ordering = ['componentGroup', 'orderNo']
        verbose_name_plural = "Component"

    def __str__(self):
        return self.internalKey


class Team(BaseModel):
    internalKey = models.CharField(max_length=2048, blank=True, null=True, unique=True)
    url = models.SlugField(max_length=10, editable=settings.DEBUG, unique=True, default=generateString, db_index=True)
    isPrivate = models.BooleanField(default=False)
    members = models.ManyToManyField(User, related_name='teamMembers')
    description = models.TextField()

    class Meta:
        verbose_name = "Team"
        verbose_name_plural = "Teams"
        index_together = [
            ("internalKey", "url"),
        ]

    def __str__(self):
        return self.internalKey


class Profile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    url = models.SlugField(max_length=10, editable=settings.DEBUG, unique=True, default=generateString, db_index=True)
    jobTitle = models.CharField(max_length=2048, blank=True, null=True)
    department = models.CharField(max_length=2048, blank=True, null=True)
    profilePicture = models.ImageField(upload_to='profile-picture', blank=True, null=True, default=getRandomAvatar)

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"

    def __str__(self):
        return self.user
